import time
import math
from artof_utils.redis_manager import redis_manager

def inject_simulated_feedback(num_sections=32):
    print("🚀 Start met het injecteren van gesimuleerde sectie-feedback...")
    print("Druk op CTRL+C om te stoppen.")
    
    counter = 0
    try:
        while True:
            for i in range(num_sections):
                wave = math.sin(counter * 0.2 + i * 0.3)
                
                val = int(127.5 * (1 + wave))
                val = max(0, min(255, val)) 
                
                key = f"plc.monitor.hitch_fb.feedback_sections.{i}"
                key2 = f"plc.monitor.hitch_rb.feedback_sections.{i}"
                redis_manager.set_value(key, val)
                redis_manager.set_value(key2, val)
            
            counter += 1
            time.sleep(0.2) 
            
    except KeyboardInterrupt:
        print("\n🛑 Simulatie van secties gestopt.")
        
        for i in range(num_sections):
            redis_manager.set_value(f"plc.monitor.hitch_fb.feedback_sections.{i}", 0)
            redis_manager.set_value(f"plc.monitor.hitch_rb.feedback_sections.{i}", 0)
        print("Alle secties zijn gereset naar 0.")

if __name__ == "__main__":
    inject_simulated_feedback()