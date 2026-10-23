#!/usr/bin/env bash
set -euo pipefail

# install.sh — Cross-platform installer for the LinkedIn Agent Skill Pack
# Detects Claude Code, Antigravity, and OpenCode, then installs skills
# to each platform's config directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
VOICE_TEMPLATE="$SCRIPT_DIR/templates/voice.md"

# Platform config directories
CLAUDE_DIR="$HOME/.claude"
GEMINI_DIR="$HOME/.gemini"
OPENCODE_DIR="$HOME/.config/opencode"

SKILLS=(
  li-audit
  li-carousel
  li-comment
  li-dm
  li-human
  li-inbox
  li-plan
  li-post
  li-profile
  li-reply
  li-repurpose
)

installed=0

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}LinkedIn Agent Skill Pack — Installer${NC}"
echo "======================================="
echo ""

install_for_platform() {
  local platform_name="$1"
  local config_dir="$2"
  local skills_subdir="$3"

  if [ ! -d "$config_dir" ]; then
    echo -e "${YELLOW}⏭  $platform_name:${NC} config directory not found ($config_dir). Skipping."
    return
  fi

  echo -e "${GREEN}✓  $platform_name detected${NC} ($config_dir)"

  # Create skills directory
  local target_skills="$config_dir/$skills_subdir"
  mkdir -p "$target_skills"

  # Copy skills
  local count=0
  for skill in "${SKILLS[@]}"; do
    if [ -d "$SKILLS_DIR/$skill" ]; then
      cp -r "$SKILLS_DIR/$skill" "$target_skills/"
      ((++count))
    fi
  done

  echo "   → Installed $count skills to $target_skills/"

  # Copy voice template
  local linkedin_dir="$config_dir/linkedin"
  mkdir -p "$linkedin_dir"

  if [ ! -f "$linkedin_dir/voice.md" ]; then
    cp "$VOICE_TEMPLATE" "$linkedin_dir/voice.md"
    echo "   → Copied voice template to $linkedin_dir/voice.md"
    echo -e "   ${YELLOW}⚠  Fill in voice.md — this is what makes the skills sound like you.${NC}"
  else
    echo "   → voice.md already exists at $linkedin_dir/voice.md (kept existing)"
  fi

  echo ""
  ((++installed))
}

# Detect and install for each platform
install_for_platform "Claude Code" "$CLAUDE_DIR" "skills"
install_for_platform "Antigravity" "$GEMINI_DIR" "config/skills"
install_for_platform "OpenCode"    "$OPENCODE_DIR" "skills"

echo "---------------------------------------"

if [ "$installed" -eq 0 ]; then
  echo -e "${RED}No supported platforms found.${NC}"
  echo ""
  echo "Expected one of:"
  echo "  • Claude Code  → $CLAUDE_DIR"
  echo "  • Antigravity   → $GEMINI_DIR"
  echo "  • OpenCode      → $OPENCODE_DIR"
  echo ""
  echo "Create the config directory for your platform and run this again,"
  echo "or copy the skills manually from skills/ to your config."
  exit 1
fi

echo -e "${GREEN}Done.${NC} Installed to $installed platform(s)."
echo ""
echo "Next steps:"
echo "  1. Fill in your voice.md (see above)"
echo "  2. Try: ask your agent to \"write a LinkedIn post about [your topic]\""
echo ""
