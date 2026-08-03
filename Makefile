.PHONY: up down backend frontend migrate logs status
 
BACKEND_DIR=backend
FRONTEND_DIR=frontend
PID_DIR=.pids
 
up:
	@mkdir -p $(PID_DIR)
	@echo "Starting backend..."
	@cd $(BACKEND_DIR) && ( . venv/bin/activate && nohup uvicorn app.main:app --reload --port 8000 > ../$(PID_DIR)/backend.log 2>&1 & echo $$! > ../$(PID_DIR)/backend.pid )
	@echo "Starting frontend..."
	@cd $(FRONTEND_DIR) && ( nohup npm run dev > ../$(PID_DIR)/frontend.log 2>&1 & echo $$! > ../$(PID_DIR)/frontend.pid )
	@sleep 1
	@echo "Backend:  http://localhost:8000/docs  (pid $$(cat $(PID_DIR)/backend.pid))"
	@echo "Frontend: http://localhost:3000        (pid $$(cat $(PID_DIR)/frontend.pid))"
 
down:
	@if [ -f $(PID_DIR)/backend.pid ]; then kill $$(cat $(PID_DIR)/backend.pid) 2>/dev/null || true; rm -f $(PID_DIR)/backend.pid; echo "Backend stopped"; fi
	@if [ -f $(PID_DIR)/frontend.pid ]; then kill $$(cat $(PID_DIR)/frontend.pid) 2>/dev/null || true; rm -f $(PID_DIR)/frontend.pid; echo "Frontend stopped"; fi
 
status:
	@if [ -f $(PID_DIR)/backend.pid ] && kill -0 $$(cat $(PID_DIR)/backend.pid) 2>/dev/null; then echo "Backend running (pid $$(cat $(PID_DIR)/backend.pid))"; else echo "Backend not running"; fi
	@if [ -f $(PID_DIR)/frontend.pid ] && kill -0 $$(cat $(PID_DIR)/frontend.pid) 2>/dev/null; then echo "Frontend running (pid $$(cat $(PID_DIR)/frontend.pid))"; else echo "Frontend not running"; fi
 
logs:
	@tail -f $(PID_DIR)/backend.log $(PID_DIR)/frontend.log
 
backend:
	@cd $(BACKEND_DIR) && . venv/bin/activate && uvicorn app.main:app --reload --port 8000
 
frontend:
	@cd $(FRONTEND_DIR) && npm run dev
 
migrate:
	@cd $(BACKEND_DIR) && . venv/bin/activate && alembic upgrade head