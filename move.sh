#!/bin/bash
move_file() {
    if git ls-files --error-unmatch "$1" > /dev/null 2>&1; then
        git mv "$1" "$2"
    else
        mv "$1" "$2"
    fi
}

move_file "app/routers/auth.py" "backend/src/api/auth.py"
move_file "app/routers/reports.py" "backend/src/api/reports.py"
move_file "app/routers/repos.py" "backend/src/api/repos.py"
move_file "app/routers/scan.py" "backend/src/api/scan.py"
move_file "app/routers/webhook.py" "backend/src/api/webhook.py"
move_file "app/routers/__init__.py" "backend/src/api/__init__.py"

move_file "app/services/github_service.py" "backend/src/services/github_service.py"
move_file "app/services/memory.py" "backend/src/services/memory.py"
move_file "app/services/report_generator.py" "backend/src/services/report_generator.py"
move_file "app/services/scanner.py" "backend/src/services/scanner.py"
move_file "app/services/__init__.py" "backend/src/services/__init__.py"

move_file "app/utils/diff_parser.py" "backend/src/utils/diff_parser.py"
move_file "app/utils/__init__.py" "backend/src/utils/__init__.py"

move_file "app/main.py" "backend/src/main.py"
move_file "app/config.py" "backend/src/core/config.py"
move_file "app/auth.py" "backend/src/core/auth.py"
move_file "app/database.py" "backend/src/database/session.py"
move_file "app/models.py" "backend/src/models/domain.py"
move_file "app/schemas.py" "backend/src/models/schemas.py"
move_file "app/__init__.py" "backend/src/__init__.py"
touch backend/src/core/__init__.py backend/src/database/__init__.py backend/src/models/__init__.py

move_file "requirements.txt" "backend/requirements.txt"
move_file "patchwatch.db" "data/sqlite/patchwatch.db"

# Remove old app directory
rm -rf app
