import sys, traceback
sys.path.insert(0, r'D:\XM\smart-doc-qa')
try:
    from app.services import qa_service
    print('SUCCESS: qa_service imported')
except Exception as e:
    print('ERROR:', e)
    traceback.print_exc()
