#!/bin/bash
set -euo pipefail

# WARPCORE Framer - Framework Generator
# Usage: fork.sh <CURRENT_NAME> <TARGET_NAME>
# Example: fork.sh WARPCORE MyApp
# 
# This creates ../TARGET_NAME/ with complete skeleton rebranded

if [ $# -ne 2 ]; then
    echo "❌ Usage: $0 <CURRENT_NAME> <TARGET_NAME>"
    echo "💡 Example: $0 WARPCORE MyApp"
    echo "🎯 This will create ../TARGET_NAME/ with complete skeleton"
    exit 1
fi

CURRENT_NAME="$1"
TARGET_NAME="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PARENT_DIR="$(cd "$SOURCE_DIR/.." && pwd)"
TARGET_DIR="$PARENT_DIR/$TARGET_NAME"

echo "🚀 Framework Framer - $CURRENT_NAME → $TARGET_NAME"
echo "📁 Source: $SOURCE_DIR"
echo "📁 Target: $TARGET_DIR"

# Check if target already exists
if [ -d "$TARGET_DIR" ]; then
    echo "❌ Target directory already exists: $TARGET_DIR"
    exit 1
fi

# Validate target name
if ! [[ "$TARGET_NAME" =~ ^[A-Za-z][A-Za-z0-9_-]*$ ]]; then
    echo "❌ Invalid target name: $TARGET_NAME"
    exit 1
fi

# Detect main script file
MAIN_SCRIPT="${CURRENT_NAME,,}.py"
if [ ! -f "$SOURCE_DIR/$MAIN_SCRIPT" ]; then
    echo "❌ Main script not found: $SOURCE_DIR/$MAIN_SCRIPT"
    exit 1
fi

cd "$SOURCE_DIR"
mkdir -p "$TARGET_DIR"

echo "🔄 Copying skeleton (excluding caches)..."

# Use rsync for efficient copying with exclusions
rsync -av \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='.pytest_cache/' \
    --exclude='dist/' \
    --exclude='build/' \
    --exclude='.dist/' \
    --exclude='venv/' \
    --exclude='env/' \
    --exclude='.env/' \
    --exclude='cache/' \
    --exclude='.cache/' \
    --exclude='*.log' \
    --exclude='tmp/' \
    --exclude='.tmp/' \
    --exclude='llm-collector/results.json' \
    --exclude='.data/' \
    --exclude='*.dmg' \
    --exclude='*.pkg' \
    --exclude='*.app' \
    --exclude='test-results/' \
    --exclude='playwright-report/' \
    --exclude='.playwright/' \
    "$SOURCE_DIR/" "$TARGET_DIR/"

echo "✅ $(find "$TARGET_DIR" -type f | wc -l | tr -d ' ') files copied"

echo "🎨 Rebranding: $CURRENT_NAME → $TARGET_NAME..."

cd "$TARGET_DIR"

# Generate all possible case variations
OLD_NAME="$CURRENT_NAME"
NEW_NAME="$TARGET_NAME"

# Core variations
OLD_UPPER="$OLD_NAME"
NEW_UPPER="${NEW_NAME^^}"

OLD_LOWER="${OLD_NAME,,}"
NEW_LOWER="${NEW_NAME,,}"

OLD_TITLE="${OLD_NAME^}"
NEW_TITLE="${NEW_NAME^}"

# Skip complex camel case for now - keep it simple

# Also handle lowercase compact variations
OLD_COMPACT="${CURRENT_NAME,,}"
NEW_COMPACT="${TARGET_NAME,,}"

echo "🔄 Replacing content in files..."

# Function to safely replace in all text files
replace_in_all_files() {
    local old="$1"
    local new="$2"
    
    # Use simpler approach
    for ext in py js json md html css txt yml yaml sh config spec sql; do
        find . -name "*.$ext" \
            ! -path "./.git/*" \
            ! -path "./node_modules/*" \
            ! -path "./__pycache__/*" \
            ! -path "./venv/*" \
            ! -path "./dist/*" \
            ! -path "./build/*" \
            -exec sed -i '' "s/$old/$new/g" {} + 2>/dev/null || true
    done
      
    echo "✅ $old → $new"
}

# Replace all variations
replace_in_all_files "$OLD_UPPER" "$NEW_UPPER"
replace_in_all_files "$OLD_LOWER" "$NEW_LOWER" 
replace_in_all_files "$OLD_TITLE" "$NEW_TITLE"
replace_in_all_files "$OLD_COMPACT" "$NEW_COMPACT"

# Special case: main script renaming
MAIN_SCRIPT="${OLD_COMPACT}.py"
NEW_SCRIPT="${NEW_COMPACT}.py"
if [ -f "$MAIN_SCRIPT" ]; then
    mv "$MAIN_SCRIPT" "$NEW_SCRIPT"
    echo "📄 $MAIN_SCRIPT → $NEW_SCRIPT"
fi

# Rename directories that contain current name
echo "🔄 Renaming directories..."
find . -type d -name "*${OLD_COMPACT}*" 2>/dev/null | sort -r | while read -r dir; do
    new_dir=$(echo "$dir" | sed "s/${OLD_COMPACT}/${NEW_COMPACT}/g")
    if [ "$dir" != "$new_dir" ] && [ ! -d "$new_dir" ]; then
        mv "$dir" "$new_dir" 2>/dev/null
        echo "📁 $(basename "$dir") → $(basename "$new_dir")"
    fi
done

# Rename files that contain current name
echo "🔄 Renaming files..."
find . -type f -name "*${OLD_COMPACT}*" 2>/dev/null | while read -r file; do
    new_file=$(echo "$file" | sed "s/${OLD_COMPACT}/${NEW_COMPACT}/g")
    if [ "$file" != "$new_file" ] && [ ! -f "$new_file" ]; then
        mv "$file" "$new_file" 2>/dev/null
        echo "📄 $(basename "$file") → $(basename "$new_file")"
    fi
done

# Also handle uppercase case in filenames
find . -type f -name "*${OLD_UPPER}*" 2>/dev/null | while read -r file; do
    new_file=$(echo "$file" | sed "s/${OLD_UPPER}/${NEW_UPPER}/g")
    if [ "$file" != "$new_file" ] && [ ! -f "$new_file" ]; then
        mv "$file" "$new_file" 2>/dev/null
        echo "📄 $(basename "$file") → $(basename "$new_file")"
    fi
done

echo "🧩 Final cleanup..."
# Clean up any remaining cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true

# Create a .forked file with metadata
cat > ".forked" << EOF
# $TARGET_NAME - Forked from $CURRENT_NAME
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Original: $CURRENT_NAME Framework
# Fork: $TARGET_NAME
# 
# This is a complete $CURRENT_NAME skeleton rebranded as $TARGET_NAME
# You can now maintain this independently and fork in time
EOF

echo ""
echo "🎉 SUCCESS! Framework generation complete!"
echo "📍 Your new framework: $TARGET_DIR"
echo "🏃 Next steps:"
echo "   1. cd $TARGET_DIR"
echo "   2. python ${NEW_COMPACT}.py --help"
echo "   3. Start customizing your framework!"
echo ""
echo "🚀 Your $TARGET_NAME framework includes:"
echo "   • Complete PAP architecture"
echo "   • Agency system with 10+ AI agents"
echo "   • Multi-deployment modes"
echo "   • License management system"
echo "   • Configuration management"
echo "   • Build pipelines"
echo ""
echo "📝 All $CURRENT_NAME references replaced with $TARGET_NAME"
echo "🔄 Fork in time and maintain independently!"
echo ""
echo "✨ Happy coding with your new $TARGET_NAME framework! ✨"
