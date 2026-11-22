#!/usr/bin/env bash
set -u

# Ensure GNU grep with PCRE support is used on macOS if installed via Homebrew
if [ -d "/opt/homebrew/opt/grep/libexec/gnubin" ]; then
  export PATH="/opt/homebrew/opt/grep/libexec/gnubin:$PATH"
fi

SRC="${1:-src}"
OUT="${2:-dist}"
TOKENS="${3:-src/styles/tokens.css}"
fail=0

check() {
  local desc="$1" pat="$2"; shift 2
  local exclude="--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist"
  if grep -RInP $exclude "$pat" "$@" 2>/dev/null | grep -q .; then
    echo "FAIL: $desc"; grep -RInP $exclude "$pat" "$@" 2>/dev/null | head -20; fail=1
  else echo "PASS: $desc"; fi
}

EX="--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude=*.png --exclude=*.jpg --exclude=*.ico --exclude=*.woff2"

check "no gradients"                  '(linear|radial|conic)-gradient|bg-gradient|from-\w+-\d+|to-\w+-\d+' "$SRC" "$OUT"
check "no pill radii (>6px)"          'border-radius:\s*(9999px|999px|50%|1[0-9]px|[2-9][0-9]px|[7-9]px|[0-9.]+rem)' "$SRC" "$OUT"
check "no purple/violet/indigo"       '(?i)\b(purple|violet|indigo|fuchsia|magenta)\b|#(8b5cf6|7c3aed|6d28d9|a855f7|6366f1|4f46e5|818cf8|c084fc)' "$SRC" "$OUT"
check "no em or en dashes"            '[\x{2014}\x{2013}]' "$SRC" "$OUT"
check "no emoji"                      '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B50}\x{1F000}-\x{1F2FF}]' "$SRC" "$OUT"
check "no builder watermark"          '(?i)made with (ai|claude|gemini|antigravity|lovable|bolt|v0)|built with (ai|claude|gemini|antigravity)|name="generator"' "$SRC" "$OUT"
check "no scroll-driven effects"      '(?i)IntersectionObserver|scroll-timeline|animation-timeline|parallax|ScrollTrigger|data-aos|\bAOS\b|framer-motion.*whileInView' "$SRC" "$OUT"
check "no custom cursor"              '(?i)cursor:\s*url\(|cursor:\s*none|mousemove.*(cursor|follow|trail)|custom-cursor' "$SRC" "$OUT"
check "no fake social proof words"    '(?i)testimonial|trusted by|join \d|customers served|happy (users|customers)|\b\d+k?\+? (teams|companies|users) (trust|use)' "$SRC" "$OUT"
check "no blocklisted copy"           '(?i)supercharge|unlock the|unleash|revolutioni[sz]e|game-?changing|cutting-edge|next-?gen(eration)?|seamless|effortless|empower|elevate your|leverage|harness|\bdelve\b|all-in-one|to the next level|transform the way' "$SRC" "$OUT"
check "no third-party font CDNs"      'fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit' "$SRC" "$OUT"
check "only allowed SVG icons"        'id="(?!i-star|i-star-filled|i-arrow-up-right)[a-zA-Z0-9_-]+"' "$SRC/static/assets/icons.svg"
check "no dark theme CSS"             '\[data-theme="dark"\]|@media\s*\(prefers-color-scheme:\s*dark\)' "$SRC" "$OUT"
check "no stock/AI imagery tags in app (review any hit)" '<img\s' "$SRC/app" "$SRC/components" 2>/dev/null
# hex colors allowed only in the tokens file
if grep -RInP $EX '(?<![\w-])#[0-9a-fA-F]{6}\b|(?<![\w-])#[0-9a-fA-F]{3}\b' "$SRC" 2>/dev/null | grep -v "$TOKENS" | grep -q .; then
  echo "FAIL: hard-coded hex outside tokens"; grep -RInP $EX '(?<![\w-])#[0-9a-fA-F]{6}\b' "$SRC" | grep -v "$TOKENS" | head -20; fail=1
else echo "PASS: hex colors only in tokens"; fi
# band background is the one allowed literal; it must be a token too
for f in favicon.svg favicon.ico apple-touch-icon.png site.webmanifest robots.txt sitemap.xml; do
  find "$OUT" -name "$f" | grep -q . && echo "PASS: $f present" || { echo "FAIL: $f missing"; fail=1; }
done
for p in privacy terms; do
  find "$OUT" -path "*$p*" \( -name index.html -o -name "$p.html" \) | grep -q . && echo "PASS: /$p built" || { echo "FAIL: /$p missing"; fail=1; }
done
grep -RIn "TODO(owner)" "$OUT" 2>/dev/null | grep -q . && { echo "FAIL: unresolved TODO(owner) in build"; fail=1; } || echo "PASS: no TODO(owner) in build"
exit $fail
