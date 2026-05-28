from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import tempfile
import shutil
import os
import json

app = FastAPI()


@app.post("/extract")
async def extract_files(
        api_key: str = Form(...),
        model_name: str = Form("gpt-4.1"),  # 新增，默认推荐 gpt-4.1
        files: List[UploadFile] = File(...)
):
    temp_paths = []

    try:
        for file in files:
            suffix = os.path.splitext(file.filename)[1].lower()
            with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix
            ) as tmp:
                shutil.copyfileobj(file.file, tmp)
                temp_paths.append(tmp.name)

        # 导入并调用优化后的 whole_pipeline
        from core import whole_pipeline

        results = whole_pipeline(
            api_key=api_key,
            model_name=model_name,
            list_of_files=temp_paths
        )

        # 可选：保存结果到临时文件供下载
        output_path = "results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "num_reactions": len(results),
            "results": results,
            "message": f"成功提取 {len(results)} 个反应"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "处理过程中发生错误"
        }

    finally:
        # 清理临时文件
        for path in temp_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )