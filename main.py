# Entry point: start agents, web UI, and simple console REPL
import threading, time, os
from core.brain import start_agents, stop_agents
from ui.webui import run_server
from ui.voice import speak, input_with_voice_fallback
from core.memory import add_episode
from config import HOST, PORT

def start_ui():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    print(f"Web UI available at http://{HOST}:{PORT}")

if __name__ == '__main__':
    print('Starting Sentience Core...')
    planner, researcher, executor, critic = start_agents()
    start_ui()
    speak('Sentience Core online. Ready.')
    try:
        while True:
            txt = input_with_voice_fallback()
            if not txt:
                continue
            if txt.lower().strip() in ('quit','exit','stop'):
                print('Exiting...')
                break
            # submit to planner via goal queue
            from core.brain import GOAL_QUEUE
            GOAL_QUEUE.put(txt)
            add_episode('user', txt)
            print('Goal submitted:', txt)
    except KeyboardInterrupt:
        print('Interrupted, shutting down.')
    finally:
        stop_agents(planner, researcher, executor, critic)
        time.sleep(1)
        print('Goodbye.')
