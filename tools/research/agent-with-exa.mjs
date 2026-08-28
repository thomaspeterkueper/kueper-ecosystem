#!/usr/bin/env node

/**
 * KUEPER research-agent wrapper with Exa external evidence prefetch.
 *
 * The existing research executor invokes the command configured in
 * KUEPER_RESEARCH_AGENT_CMD with the research prompt as its final argument.
 * This wrapper keeps that contract, optionally enriches the prompt with a
 * live Exa evidence packet through Vercel AI Gateway, then delegates to the
 * existing Claude Code frontend used by the research loop.
 *
 * Exa output is discovery material only. The downstream agent must still
 * perform claim/source mapping and the existing candidate validation gates.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const policyPath = path.join(root, 'research', 'policy.json');
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const evidencePolicy = policy.external_evidence ?? {};
const evidenceProfiles = policy.evidence_profiles ?? {};

const originalPrompt = process.argv.slice(2).join(' ').trim();
if (!originalPrompt) {
  console.error('agent-with-exa: missing research prompt');
  process.exit(2);
}

function field(prompt, label) {
  const match = prompt.match(new RegExp(`^${label}:\\s*(.+)$`, 'mi'));
  return match?.[1]?.trim() ?? '';
}

function uniqueUrls(text) {
  return [...new Set(text.match(/https?:\/\/[^\s)>\]"']+/g) ?? [])];
}

function resolveProfile(sourceProject) {
  const explicit = field(originalPrompt, 'Evidence profile');
  const project = (policy.eligible_projects ?? []).find((entry) => entry.id === sourceProject);
  const name = explicit || project?.evidence_profile || 'general';
  return { name, config: evidenceProfiles[name] ?? evidenceProfiles.general ?? {} };
}

function scoutDecision(text, urlCount, minimumUrls) {
  const followUp = text.match(/Follow-up search needed:\s*(yes|no)/i)?.[1]?.toLowerCase();
  const confidence = text.match(/Research confidence:\s*(high|medium|low)/i)?.[1]?.toLowerCase();

  if (!text.trim()) return { escalate: true, reason: 'initial scout returned no synthesis text' };
  if (urlCount < minimumUrls) {
    return {
      escalate: true,
      reason: `initial scout returned ${urlCount} URL(s), below minimum ${minimumUrls}`,
    };
  }
  if (followUp === 'yes') return { escalate: true, reason: 'scout explicitly requested follow-up search' };
  if (confidence === 'low') return { escalate: true, reason: 'scout confidence is low' };
  return { escalate: false, reason: 'initial evidence packet is sufficient' };
}

async function buildEvidencePacket() {
  if (evidencePolicy.enabled === false) return null;

  const auth = process.env.AI_GATEWAY_API_KEY || process.env.VERCEL_OIDC_TOKEN;
  if (!auth) {
    console.error('agent-with-exa: AI Gateway credential missing; continuing without Exa evidence');
    return null;
  }

  const { generateText, gateway, stepCountIs } = await import('ai');

  const researchId = field(originalPrompt, 'Research ID') || 'unknown';
  const sourceProject = field(originalPrompt, 'Source project') || 'unknown';
  const question = field(originalPrompt, 'Question');
  const whyNow = field(originalPrompt, 'Why now');
  const requestedLanguages = field(originalPrompt, 'Requested source languages') || 'de, en';
  const preclassifiedClaims = field(originalPrompt, 'Preclassified claim classes') || '[]';
  const realWorldAnchor = field(originalPrompt, 'Real-world anchor') || 'none specified';
  const publicationRouteHint = field(originalPrompt, 'Publication route hint') || 'none';
  const { name: profileName, config: profile } = resolveProfile(sourceProject);

  const model =
    process.env.KUEPER_EVIDENCE_MODEL ||
    evidencePolicy.model ||
    'deepseek/deepseek-v4-flash-0731';
  const numResults = Number(
    process.env.KUEPER_EVIDENCE_NUM_RESULTS || profile.exa_num_results || evidencePolicy.num_results || 6,
  );
  const baseSteps = Math.max(
    2,
    Number(process.env.KUEPER_EVIDENCE_BASE_STEPS || profile.exa_base_steps || 2),
  );
  const maxSteps = Math.max(
    baseSteps,
    Number(process.env.KUEPER_EVIDENCE_MAX_STEPS || profile.exa_max_steps || evidencePolicy.max_steps || 4),
  );
  const followUpSteps = Math.max(0, maxSteps - baseSteps);
  const minimumUrls = Number(profile.minimum_urls || evidencePolicy.minimum_urls || 2);
  const preferredSourceTypes = (profile.preferred_source_types ?? []).join(', ');
  const profileGuidance = profile.scout_guidance || 'Apply rigorous source criticism and preserve uncertainty.';
  const claimClassRules = JSON.stringify(profile.claim_classes ?? {});
  const claimAliases = JSON.stringify(profile.claim_aliases ?? {});

  const tools = {
    exa_search: gateway.tools.exaSearch({
      type: evidencePolicy.search_type || 'auto',
      numResults,
    }),
  };

  const providerOptions = {
    gateway: {
      user: 'kueper-research-loop',
      tags: ['kueper', 'external-evidence', 'exa', `project:${sourceProject}`, `profile:${profileName}`],
    },
  };

  const initialPrompt = `You are the external-evidence scout for the KUEPER research pipeline.

Research ID: ${researchId}
Source project: ${sourceProject}
Question: ${question}
Why now: ${whyNow}
Requested discovery languages: ${requestedLanguages}
Evidence profile: ${profileName}
Pre-research claim classification: ${preclassifiedClaims}
Real-world anchor to research: ${realWorldAnchor}
Publication-route hint: ${publicationRouteHint}
Claim-class rules: ${claimClassRules}
Claim aliases: ${claimAliases}
Preferred source types: ${preferredSourceTypes || 'not specified'}
Profile-specific guidance: ${profileGuidance}

The claim classes were assigned before external research. Preserve the epistemic boundary: search external evidence for the real-world anchor, premises, constraints, attestation, counterevidence or falsifiability question. Do not use Exa results to validate fictional canon or authorial/work-setting claims. For theoretical, hypothetical or speculative claims, sources can constrain or motivate the claim but cannot turn it into an established result by source count.

Cost discipline is part of the task. Perform exactly one Exa search in the first tool step, then synthesize the result in the next step. Do not perform a second search during this initial pass. A separate adaptive follow-up pass is available if the evidence is genuinely insufficient or conflicting.

Prefer primary sources, peer-reviewed papers, official institutions, standards bodies, academic publishers, and original technical documentation. Secondary sources may be included only when useful for orientation or disagreement. When the profile requires freshness checking, actively notice newer results, corrections, null findings or superseding publications. When it requires conflict checking, surface serious counterevidence rather than optimizing for confirmation.

Return a compact evidence packet in Markdown with exactly these sections:
## Search summary
## Claim classification
Restate the pre-research class for each material claim and say what part external evidence can actually assess.
## Candidate claims
For each material externally assessable claim state whether the source support looks established, inferential, contested, or insufficient.
## Conflicts and uncertainty
## Freshness check
State whether newer evidence materially changes the picture; say "not material" when appropriate.
## Sources
Number every source and include its exact title, author/institution when available, publication date when available, exact URL, source language, source type, and preprint/peer-review status when relevant.
## Scout decision
Follow-up search needed: yes|no
Research confidence: high|medium|low
Reason: one concise sentence.

Set "Follow-up search needed" to yes only when a material conflict remains unresolved, source quality is inadequate for the evidence profile, or the minimum source coverage is clearly not met. Do not request follow-up merely to collect more sources when the current evidence already answers the question adequately.

Do not fabricate citations, URLs, dates, authors, quotations, or source contents. This packet is discovery material for a second research agent, not a canonical conclusion and not a publication decision.`;

  const initial = await generateText({
    model,
    system:
      `Use Exa search to ground the response in current external sources. Apply evidence profile ${profileName} and preserve the supplied pre-research claim classification. Use one search pass first, then synthesize. Preserve uncertainty and source provenance.`,
    prompt: initialPrompt,
    tools,
    prepareStep: ({ stepNumber }) =>
      stepNumber === 0
        ? { toolChoice: { type: 'tool', toolName: 'exa_search' } }
        : { toolChoice: 'auto' },
    stopWhen: stepCountIs(baseSteps),
    providerOptions,
  });

  const initialSearchResults = initial.steps
    .flatMap((step) => step.staticToolResults ?? [])
    .filter((toolResult) => toolResult.toolName === 'exa_search');
  const initialUrls = uniqueUrls(initial.text);

  if (initialSearchResults.length < 1) {
    throw new Error('Exa scout returned no exa_search tool result');
  }

  const decision = scoutDecision(initial.text, initialUrls.length, minimumUrls);
  let finalText = initial.text.trim();
  let searchResults = [...initialSearchResults];
  let escalated = false;
  let escalationReason = null;

  if (decision.escalate && followUpSteps >= 2) {
    escalated = true;
    escalationReason = decision.reason;

    const followUpPrompt = `You are performing the adaptive follow-up pass for the KUEPER external-evidence scout.

Research ID: ${researchId}
Source project: ${sourceProject}
Question: ${question}
Evidence profile: ${profileName}
Pre-research claim classification: ${preclassifiedClaims}
Real-world anchor to research: ${realWorldAnchor}
Publication-route hint: ${publicationRouteHint}
Profile-specific guidance: ${profileGuidance}
Reason for follow-up: ${decision.reason}

Initial evidence packet:
---
${initial.text.trim()}
---

Perform exactly one additional Exa search targeted at the unresolved conflict, missing strong source, freshness issue, counterevidence, or coverage gap identified above. Do not repeat the same broad query unless necessary. Preserve the original epistemic class: do not upgrade theory/speculation/fiction because more sources were found. Then synthesize only the incremental findings and state whether the follow-up resolved the issue.

Return Markdown with these sections:
## Follow-up search summary
## Additional or corrected claims
## Remaining conflicts and uncertainty
## Additional sources
Include exact URLs and source types.
## Follow-up decision
Resolved sufficiently: yes|no
Research confidence: high|medium|low

Do not fabricate citations, URLs, dates, authors, quotations, or source contents.`;

    const followUp = await generateText({
      model,
      system:
        `Resolve only the specific evidence gap from the first pass. Apply evidence profile ${profileName} without changing the epistemic class by source count. Use exactly one additional Exa search, then synthesize.`,
      prompt: followUpPrompt,
      tools,
      prepareStep: ({ stepNumber }) =>
        stepNumber === 0
          ? { toolChoice: { type: 'tool', toolName: 'exa_search' } }
          : { toolChoice: 'auto' },
      stopWhen: stepCountIs(followUpSteps),
      providerOptions,
    });

    const followUpSearchResults = followUp.steps
      .flatMap((step) => step.staticToolResults ?? [])
      .filter((toolResult) => toolResult.toolName === 'exa_search');
    if (followUpSearchResults.length < 1) {
      throw new Error('Adaptive Exa follow-up returned no exa_search tool result');
    }

    searchResults = [...searchResults, ...followUpSearchResults];
    finalText = `${finalText}\n\n---\n## Adaptive follow-up\n\n${followUp.text.trim()}`.trim();
  }

  const urls = uniqueUrls(finalText);
  if (urls.length < minimumUrls) {
    throw new Error(`Exa scout returned only ${urls.length} source URL(s); minimum is ${minimumUrls}`);
  }

  return {
    provider: 'exa',
    transport: 'vercel-ai-gateway',
    model,
    profile: profileName,
    preclassifiedClaims,
    publicationRouteHint,
    baseSteps,
    maxSteps,
    escalated,
    escalationReason,
    searchCalls: searchResults.length,
    urlCount: urls.length,
    text: finalText,
  };
}

function runUnderlyingAgent(prompt) {
  const command = process.env.KUEPER_SYNTHESIS_AGENT_BIN || 'claude';
  const args = ['-p', '--dangerously-skip-permissions', prompt];
  const child = spawnSync(command, args, {
    env: process.env,
    stdio: 'inherit',
  });

  if (child.error) {
    console.error(`agent-with-exa: failed to start ${command}: ${child.error.message}`);
    return 127;
  }
  return child.status ?? 1;
}

try {
  const packet = await buildEvidencePacket();

  if (process.env.KUEPER_EXA_SMOKE_ONLY === '1') {
    if (!packet) {
      throw new Error('Exa smoke test produced no evidence packet');
    }
    console.log(
      JSON.stringify(
        {
          ok: true,
          provider: packet.provider,
          transport: packet.transport,
          model: packet.model,
          profile: packet.profile,
          preclassifiedClaims: packet.preclassifiedClaims,
          publicationRouteHint: packet.publicationRouteHint,
          baseSteps: packet.baseSteps,
          maxSteps: packet.maxSteps,
          escalated: packet.escalated,
          searchCalls: packet.searchCalls,
          urlCount: packet.urlCount,
        },
        null,
        2,
      ),
    );
    process.exit(0);
  }

  let augmentedPrompt = originalPrompt;

  if (packet) {
    augmentedPrompt += `\n\n---\n## External evidence discovery packet (Exa via Vercel AI Gateway)\n\nThis packet is non-canonical discovery material. Treat every claim as provisional until mapped to the cited source. Preserve the pre-research epistemic classification. Prefer the packet's exact URLs as starting points, compare conflicting sources, and use live web search as an additional verification channel when available. Never elevate fictional canon, work-setting, theory or speculation to established real-world evidence merely because sources were found. Publication routing remains advisory and review-gated.\n\nProvider: ${packet.provider}\nTransport: ${packet.transport}\nScout model: ${packet.model}\nEvidence profile: ${packet.profile}\nPreclassified claims: ${packet.preclassifiedClaims}\nPublication route hint: ${packet.publicationRouteHint}\nAdaptive escalation: ${packet.escalated ? 'yes' : 'no'}\nSearch calls: ${packet.searchCalls}\nSource URLs surfaced: ${packet.urlCount}\n\n${packet.text}\n---`;
    console.error(
      `agent-with-exa: attached Exa evidence packet (${packet.searchCalls} search call(s), ${packet.urlCount} URL(s), escalated=${packet.escalated})`,
    );
  }

  process.exit(runUnderlyingAgent(augmentedPrompt));
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  const required =
    evidencePolicy.required === true || process.env.KUEPER_EXTERNAL_EVIDENCE_REQUIRED === '1';
  console.error(`agent-with-exa: Exa evidence failed: ${message}`);
  if (process.env.KUEPER_EXA_SMOKE_ONLY === '1') process.exit(4);
  if (required) process.exit(3);
  console.error('agent-with-exa: falling back to the existing research agent without Exa');
  process.exit(runUnderlyingAgent(originalPrompt));
}
