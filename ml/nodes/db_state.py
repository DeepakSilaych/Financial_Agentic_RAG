import state
from database import FinancialDatabase

def store_db_state(state: state.InternalRAGState):
    db = FinancialDatabase()
    db_state = db.get_all_reports() # list of Dict containing details of all the reports in the db 

    print(db_state)
    state['db_state'] = db_state

    return state
