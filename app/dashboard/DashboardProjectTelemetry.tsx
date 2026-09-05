"use client";

import { useEffect } from "react";

type ProjectStatus = {
  id: string;
  name: string;
  repository: string;
  open_tasks?: number;
};

type LiveTask = {
  id: string;
  external_id: string | null;
  type: string;
  status: string;
  target_project: string | null;
  repository: string | null;
  pr_url: string | null;
  blocked_reason: string | null;
};

const NON_TERMINAL = new Set(["pending", "claimed", "running", "review_pending", "blocked", "parked"]);
const PROJECT_ALIASES: Record<string, string> = {
  eco: "ecosystem",
  ecosystem: "ecosystem",
  eng: "engineering",
  engineering: "engineering",
  nox: "noxia",
  noxia: "noxia",
  ssf: "ssf",
  kg: "knowledge-graph",
  knowledgegraph: "knowledge-graph",
  ota: "ota",
  kue: "kueper-com",
  kuepercom: "kueper-com",
  tkd: "thomas-kueper-de",
  thomaskueperde: "thomas-kueper-de",
  nxu: "noxia-universe",
  noxiauniverse: "noxia-universe",
  mish: "mishkenaz",
  omni: "omnizedenz",
  avi: "avi-modell",
  kon: "contracomology",
};

function norm(value: string | null | undefined) {
  return (value || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function shortReason(reason: string) {
  const compact = reason.replace(/\s+/g, " ").trim();
  return compact.length > 92 ? `${compact.slice(0, 89)}…` : compact;
}

function targetProjectId(task: LiveTask, projects: ProjectStatus[]) {
  if (task.repository) {
    const byRepo = projects.find((p) => norm(p.repository) === norm(task.repository));
    if (byRepo) return byRepo.id;
  }
  const target = norm(task.target_project?.includes(":") ? task.target_project.split(":").pop() : task.target_project);
  const alias = PROJECT_ALIASES[target];
  if (alias) return alias;
  return projects.find((p) => norm(p.id) === target || norm(p.name) === target)?.id || null;
}

export default function DashboardProjectTelemetry() {
  useEffect(() => {
    let cancelled = false;

    async function enhance() {
      const grid = document.querySelector<HTMLElement>(".project-grid-modern");
      if (!grid) return;

      try {
        const [statusRes, tracesRes] = await Promise.all([
          fetch("/api/status", { cache: "no-store" }),
          fetch("/api/traces", { cache: "no-store" }),
        ]);
        if (!statusRes.ok || !tracesRes.ok || cancelled) return;

        const status = await statusRes.json();
        const traces = await tracesRes.json();
        const projects: ProjectStatus[] = Array.isArray(status?.projects) ? status.projects : [];
        const liveTasks: LiveTask[] = Array.isArray(traces?.tasks) ? traces.tasks : [];
        const openLive = liveTasks.filter((task) => NON_TERMINAL.has(task.status));

        const liveByProject = new Map<string, LiveTask[]>();
        for (const task of openLive) {
          const projectId = targetProjectId(task, projects);
          if (!projectId) continue;
          const current = liveByProject.get(projectId) || [];
          current.push(task);
          liveByProject.set(projectId, current);
        }

        const cards = [...grid.querySelectorAll<HTMLElement>(".project-card")];
        const projectByName = new Map(projects.map((p) => [p.name, p]));

        const ranked = cards.map((card, originalIndex) => {
          const name = card.querySelector<HTMLElement>(".name")?.textContent?.trim() || "";
          const project = projectByName.get(name);
          const live = project ? liveByProject.get(project.id) || [] : [];
          const backlog = project?.open_tasks || 0;
          const prUrls = new Set(live.map((task) => task.pr_url).filter((url): url is string => Boolean(url)));
          const blockers = live.filter((task) => Boolean(task.blocked_reason));
          const workload = backlog + live.length;

          const meta = card.querySelector<HTMLElement>(".meta");
          if (meta) {
            const labels = [...meta.querySelectorAll("span")];
            const prLabel = labels.find((el) => el.textContent?.trim() === "PRs");
            const prValue = prLabel?.nextElementSibling as HTMLElement | null;
            if (prValue && (prValue.textContent?.trim() === "—" || prUrls.size > 0)) prValue.textContent = String(prUrls.size);

            let workLabel = meta.querySelector<HTMLElement>("[data-live-workload]");
            let workValue = meta.querySelector<HTMLElement>("[data-live-workload-value]");
            if (!workLabel) {
              workLabel = document.createElement("span");
              workLabel.dataset.liveWorkload = "true";
              workLabel.textContent = "Offene Arbeit";
              meta.appendChild(workLabel);
            }
            if (!workValue) {
              workValue = document.createElement("b");
              workValue.dataset.liveWorkloadValue = "true";
              meta.appendChild(workValue);
            }
            workValue.textContent = String(workload);
          }

          card.querySelector("[data-project-blockers]")?.remove();
          if (blockers.length) {
            const box = document.createElement("div");
            box.dataset.projectBlockers = "true";
            box.className = "project-blockers";
            const distinctReasons = [...new Set(blockers.map((task) => task.blocked_reason!).filter(Boolean))];
            box.innerHTML = `<span class="project-blocker-count">${blockers.length} Blocker</span><span class="project-blocker-reason" title="${distinctReasons.join(" | ").replace(/\"/g, "&quot;")}">${shortReason(distinctReasons[0])}${distinctReasons.length > 1 ? ` · +${distinctReasons.length - 1}` : ""}</span>`;
            card.appendChild(box);
          }

          card.dataset.workload = String(workload);
          card.dataset.blockers = String(blockers.length);
          return { card, workload, blockers: blockers.length, originalIndex };
        });

        ranked.sort((a, b) => b.workload - a.workload || b.blockers - a.blockers || a.originalIndex - b.originalIndex);
        for (const item of ranked) grid.appendChild(item.card);

        const allOpenPrs = new Set(openLive.map((task) => task.pr_url).filter((url): url is string => Boolean(url)));
        for (const metric of document.querySelectorAll<HTMLElement>(".ops-summary .metric")) {
          if (metric.querySelector(".lbl")?.textContent?.trim() === "Offene PRs") {
            const value = metric.querySelector<HTMLElement>(".val");
            if (value) value.textContent = String(allOpenPrs.size);
          }
        }
      } catch {
        // Dashboard remains usable with the base projection if live enrichment fails.
      }
    }

    const timer = window.setTimeout(enhance, 120);
    const observer = new MutationObserver(() => {
      if (document.querySelector(".project-grid-modern .project-card")) enhance();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      observer.disconnect();
    };
  }, []);

  return (
    <style jsx global>{`
      .project-card { transition: border-color .16s ease, transform .16s ease; }
      .project-card[data-blockers]:not([data-blockers="0"]) { border-color: rgba(255, 115, 92, .32); }
      .project-blockers { margin: 10px 0 2px; padding: 8px 9px; border: 1px solid rgba(255, 115, 92, .25); border-radius: 7px; background: rgba(255, 90, 75, .055); display: grid; gap: 4px; }
      .project-blocker-count { color: #ff8d79; font: 700 10px var(--font-mono); text-transform: uppercase; letter-spacing: .05em; }
      .project-blocker-reason { color: #d7b2aa; font-size: 11px; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    `}</style>
  );
}
