"""Lynxfall Task Handling using rabbitmq (simple rabbitmq workers)"""
import asyncio
import importlib

def run(module_path):
    module = importlib.import_module(module_path)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(module.run_worker(loop))

        # we enter a never-ending loop that waits for data and runs
        # callbacks whenever necessary.
        loop.run_forever()
        except KeyboardInterrupt:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(module.disconnect_worker())
            except:
                pass
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}")
