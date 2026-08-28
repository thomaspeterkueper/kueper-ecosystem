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
import { generateText, gateway, stepCountIs } from 'ai';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const policyPath = path.join(root, 'research', 'policy.json');
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const evidencePolicy = policy.external_evidence ?? {};

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

async function buildEvidencePacket() {
  if (evidencePolicy.enabled === false) return null;

  const auth = process.env.AI_GATEWAY_API_KEY || process.env.VERCEL_OIDC_TOKEN;
  if (!auth) {
    console.error('agent-with-exa: AI Gateway credential missing; continuing without Exa evidence');
    return null;
  }

  const researchId = field(originalPrompt, 'Research ID') || 'unknown';
  const sourceProject = field(originalPrompt, 'Source project') || 'unknown';
  const question = field(originalPrompt, 'Question');
  const whyNow = field(originalPrompt, 'Why now');
  const requestedLanguages = field(originalPrompt, 'Requested source languages') || 'de, en';

  const model =
    process.env.KUEPER_EVIDENCE_MODEL ||
    evidencePolicy.model ||
    'google/gemini-3.5-flash-lite';
  const numResults = Number(
    process.env.KUEPER_EVIDENCE_NUM_RESULTS || evidencePolicy.num_results || 6,
  );
  const maxSteps = Number(
    process.env.KUEPER_EVIDENCE_MAX_STEPS || evidencePolicy.max_steps || 4,
  );
  const minimumUrls = Number(evidencePolicy.minimum_urls || 2);

  const prompt = `You are the external-evidence scout for the KUEPER research pipeline.

Research ID: ${researchId}
Source project: ${sourceProject}
Question: ${question}
Why now: ${whyNow}
Requested discovery languages: ${requestedLanguages}

Use the exa_search tool before answering. Search with more than one query when that materially improves coverage. Prefer primary sources, peer-reviewed papers, official institutions, standards bodies, academic publishers, and original technical documentation. Secondary sources may be included only when useful for orientation or disagreement.

Return a compact evidence packet in Markdown with exactly these sections:
## Search summary
## Candidate claims
For each material claim state whether the source support looks established, inferential, contested, or insufficient.
## Conflicts and uncertainty
## Sources
Number every source and include its exact title, author/institution when available, publication date when available, exact URL, source language, and source type.

Do not fabricate citations, URLs, dates, authors, quotations, or source contents. This packet is discovery material for a second research agent, not a canonical conclusion.`;

  const result = await generateText({
    model,
    system:
      'Use Exa search to ground the response in current external sources. Search first; synthesize second. Preserve uncertainty and source provenance.',
    prompt,
    tools: {
      exa_search: gateway.tools.exaSearch({
        type: evidencePolicy.search_type || 'auto',
        numResults,
      }),
    },
    prepareStep: ({ stepNumber }) =>
      stepNumber === 0
        ? { toolChoice: { type: 'tool', toolName: 'exa_search' } }
        : { toolChoice: 'auto' },
    stopWhen: stepCountIs(maxSteps),
    providerOptions: {
      gateway: {
        user: 'kueper-research-loop',
        tags: ['kueper', 'external-evidence', 'exa', `project:${sourceProject}`],
      },
    },
  });

  const searchResults = result.steps
    .flatMap((step) => step.staticToolResults ?? [])
    .filter((toolResult) => toolResult.toolName === 'exa_search');
  const urls = uniqueUrls(result.text);

  if (searchResults.length < 1) {
    throw new Error('Exa scout returned no exa_search tool result');
  }
  if (urls.length < minimumUrls) {
    throw new Error(`Exa scout returned only ${urls.length} source URL(s); minimum is ${minimumUrls}`);
  }

  return {
    provider: 'exa',
    transport: 'vercel-ai-gateway',
    model,
    searchCalls: searchResults.length,
    urlCount: urls.length,
    text: result.text.trim(),
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
  let augmentedPrompt = originalPrompt;

  if (packet) {
    augmentedPrompt += `\n\n---\n## External evidence discovery packet (Exa via Vercel AI Gateway)\n\nThis packet is non-canonical discovery material. Treat every claim as provisional until mapped to the cited source. Prefer the packet's exact URLs as starting points, compare conflicting sources, and use live web search as an additional verification channel when available. Never elevate fictional canon to real-world evidence.\n\nProvider: ${packet.provider}\nTransport: ${packet.transport}\nScout model: ${packet.model}\nSearch calls: ${packet.searchCalls}\nSource URLs surfaced: ${packet.urlCount}\n\n${packet.text}\n---`;
    console.error(
      `agent-with-exa: attached Exa evidence packet (${packet.searchCalls} search result(s), ${packet.urlCount} URL(s))`,
    );
  }

  process.exit(runUnderlyingAgent(augmentedPrompt));
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  const required =
    evidencePolicy.required === true || process.env.KUEPER_EXTERNAL_EVIDENCE_REQUIRED === '1';
  console.error(`agent-with-exa: Exa evidence failed: ${message}`);
  if (required) process.exit(3);
  console.error('agent-with-exa: falling back to the existing research agent without Exa');
  process.exit(runUnderlyingAgent(originalPrompt));
}
