import schedule
import time
from service.funding.generate_cmc_id_map import main as update_cmc_id_map

def job():
    print("Running daily update for SYMBOL_TO_CMC_ID...")
    update_cmc_id_map()
    print("Update completed.")

# Schedule the job to run once a day
schedule.every().day.at("00:00").do(job)
