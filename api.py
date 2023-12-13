from fastapi import FastAPI, UploadFile, File
import warnings
from time import time
import uvicorn
from predictions import getPredictions
from io import BytesIO
from starlette.responses import RedirectResponse
import concurrent.futures
import os
warnings.filterwarnings('ignore')
app_desc = """<h2>Giấy chứng nhận cơ sở an toàn thực phẩm nông lâm thủy sản - Cấp huyện</h2>"""
app = FastAPI(title="Tân Dân JSC - Demo by NĐ", description=app_desc)
@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/docs")

def process_file(file,filename):
    try:
        if not filename.endswith('.pdf'):
            raise ValueError("Vui lòng nhập vào file đúng định dạng pdf và đúng mẫu!")
        file_path = BytesIO(file)
        result = getPredictions(file_path)
        return result
    except Exception as e:
        save_directory = "file_eror"
        os.makedirs(save_directory,exist_ok=True)
        with open(os.path.join(save_directory,filename),'wb') as f:
            f.write(file)
        return {"error": True, "error_message": str(e)}
    
@app.post("/upload")
async def upload_file(files: list[UploadFile] = File(...)):
    start_time = time()
    result = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file,await file.read(),file.filename) for file in files]
        results = concurrent.futures.wait(futures)
        for futures in results.done:
            result.append(futures.result())
    end_time = time()
    response = {"results": result, "execution_time": end_time - start_time}
    for res in result:
        if "error" in res and res["error"]:
            response["error_message"] = res["error_message"]
            break
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8049)