@echo off
echo Starting Recipe Embedding Refresh...
echo Using Python environment at .euv_scrap_recipes
.euv_scrap_recipes\Scripts\python.exe scripts/refresh_embeddings.py
echo.
echo Process Complete.
pause
