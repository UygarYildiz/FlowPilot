#!/usr/bin/env node
// Belge güncellik kontrolü (ADR-006).
//   node dokuman-kontrol.mjs stop        -> Claude Code Stop hook'u
//   node dokuman-kontrol.mjs pre-commit  -> git pre-commit hook'u
// Kural: kod değiştiyse docs/DURUM.md de güncellenmiş olmalı.

import { execFileSync } from "node:child_process";
import { statSync, readFileSync } from "node:fs";
import { join } from "node:path";

const DURUM = "docs/DURUM.md";
const mode = process.argv[2] ?? "stop";

function git(args, cwd) {
  return execFileSync("git", ["-c", "core.quotePath=false", ...args], {
    cwd,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  });
}

// Belge sayılan yollar: bunlar değişince DURUM.md güncellemesi istenmez.
function isDoc(path) {
  return (
    path.startsWith("docs/") ||
    ["README.md", "CHANGELOG.md", "CLAUDE.md"].includes(path)
  );
}

function mtime(root, path) {
  try {
    return statSync(join(root, path)).mtimeMs;
  } catch {
    return null; // silinmiş dosya
  }
}

function buAyinGunlugu() {
  const d = new Date();
  return `docs/gunluk/${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}.md`;
}

function repoRoot(cwd) {
  return git(["rev-parse", "--show-toplevel"], cwd).trim();
}

// ---- Stop hook ----
function stopHook() {
  let input = {};
  try {
    input = JSON.parse(readFileSync(0, "utf8") || "{}");
  } catch {}
  // Hook zaten bir kez durdurduysa döngüye girme.
  if (input.stop_hook_active) return;

  const root = repoRoot(input.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd());
  // -z: NUL ile ayrılmış; yeniden adlandırmalarda ikinci yol da gelir.
  const raw = git(["status", "--porcelain", "-z", "-uall"], root);
  const entries = [];
  const parts = raw.split("\0").filter(Boolean);
  for (let i = 0; i < parts.length; i++) {
    const status = parts[i].slice(0, 2);
    entries.push({ status, path: parts[i].slice(3) });
    if (status.includes("R") || status.includes("C")) i++; // eski yol
  }

  const kod = entries.filter((e) => !isDoc(e.path));
  if (kod.length === 0) return;

  const durumZamani = mtime(root, DURUM) ?? 0;
  const durumDegisti = entries.some((e) => e.path === DURUM);
  const eskiKalan = kod.filter((e) => {
    const t = mtime(root, e.path);
    return t === null ? !durumDegisti : t > durumZamani;
  });
  if (eskiKalan.length === 0) return;

  const liste = eskiKalan.slice(0, 8).map((e) => `  - ${e.path}`).join("\n");
  const fazla = eskiKalan.length > 8 ? `\n  - … ve ${eskiKalan.length - 8} dosya daha` : "";
  process.stdout.write(
    JSON.stringify({
      decision: "block",
      reason:
        `Kod değişti ama ${DURUM} bu değişikliklerden sonra güncellenmedi:\n${liste}${fazla}\n\n` +
        `İşi bitirmeden önce CLAUDE.md'deki "Güncel tutma" adımlarını uygula: ` +
        `${DURUM} (tarih, şu an yapılan, sıradaki adım), ${buAyinGunlugu()} (en üste kısa kayıt), ` +
        `gerekiyorsa docs/MIMARI.md, docs/KARARLAR.md ve docs/YOL_HARITASI.md.`,
    })
  );
}

// ---- git pre-commit ----
function preCommit() {
  const root = repoRoot(process.cwd());
  const staged = git(["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRD"], root)
    .split("\0")
    .filter(Boolean);
  const kod = staged.filter((p) => !isDoc(p));
  if (kod.length === 0 || staged.includes(DURUM)) return 0;

  process.stderr.write(
    `\n[FlowPilot] Commit durduruldu: kod değişiyor ama ${DURUM} commit'te yok.\n` +
      `Belgeler kodla aynı commit'te güncellenir (CLAUDE.md, ADR-006).\n` +
      `Yapılacaklar: ${DURUM} ve ${buAyinGunlugu()} dosyasını güncelleyip 'git add' ile ekle.\n\n`
  );
  return 1;
}

try {
  if (mode === "pre-commit") process.exit(preCommit());
  stopHook();
} catch (err) {
  // Kontrolün kendisi bozulursa çalışmayı engelleme; yalnızca bildir.
  process.stderr.write(`[dokuman-kontrol] atlandı: ${err.message}\n`);
  process.exit(0);
}
