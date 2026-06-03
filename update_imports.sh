#!/bin/bash
find backend/src -type f -name "*.py" -exec sed -i \
  -e 's/from app\.config/from src.core.config/g' \
  -e 's/import app\.config/import src.core.config/g' \
  -e 's/from app\.database/from src.database.session/g' \
  -e 's/import app\.database/import src.database.session/g' \
  -e 's/from app\.models/from src.models.domain/g' \
  -e 's/import app\.models/import src.models.domain/g' \
  -e 's/from app\.schemas/from src.models.schemas/g' \
  -e 's/import app\.schemas/import src.models.schemas/g' \
  -e 's/from app\.auth/from src.core.auth/g' \
  -e 's/import app\.auth/import src.core.auth/g' \
  -e 's/from app\.routers/from src.api/g' \
  -e 's/import app\.routers/import src.api/g' \
  -e 's/from app\.services/from src.services/g' \
  -e 's/import app\.services/import src.services/g' \
  -e 's/from app\.utils/from src.utils/g' \
  -e 's/import app\.utils/import src.utils/g' \
  -e 's/from app import/from src import/g' \
  -e 's/import app/import src/g' \
  {} +
