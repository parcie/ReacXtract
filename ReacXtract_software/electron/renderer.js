const output = document.getElementById("output");
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("files");

// =========================
// 日志输出
// =========================
window.electronAPI.removeBackendLogListeners();

window.electronAPI.onBackendLog((msg) => {

  const line = document.createElement("div");

  // 错误日志红色
  if (msg.includes("[ERROR]") || msg.includes("❌")) {
    line.className = "text-red-400";
  }
  // warning 黄色
  else if (msg.includes("⚠️")) {
    line.className = "text-yellow-400";
  }
  // 正常日志
  else {
    line.className = "text-gray-300";
  }

  line.textContent = msg;

  output.appendChild(line);

  // 自动滚动到底部
  output.scrollTop = output.scrollHeight;
});


// =========================
// 拖拽上传
// =========================

// 点击区域 -> 打开文件选择
dropZone.addEventListener("click", () => {
  fileInput.click();
});

// 拖拽进入
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

// 拖拽离开
dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

// 放下文件
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");

  fileInput.files = e.dataTransfer.files;

  updateFileDisplay();
});

// 文件选择后更新显示
fileInput.addEventListener("change", () => {
  updateFileDisplay();
});


// =========================
// 显示已选文件
// =========================
function updateFileDisplay() {

  const files = fileInput.files;

  if (!files || files.length === 0) return;

  let html = `
    <div class="mt-3 text-left">
      <div class="text-sm text-indigo-300 mb-2">
        Selected Files:
      </div>
  `;

  for (const file of files) {
    html += `
      <div class="text-xs text-gray-300 truncate">
        • ${file.name}
      </div>
    `;
  }

  html += `</div>`;

  dropZone.innerHTML = html;
}


// =========================
// 主运行函数
// =========================
async function run() {

  const apiKey = document.getElementById("apiKey").value;
  const files = fileInput.files;

  output.innerHTML = "";

  // 检查 API KEY
  if (!apiKey) {
    output.innerHTML = `
      <div class="text-red-400">
        Please input API Key
      </div>
    `;
    return;
  }

  // 检查文件
  if (!files || files.length === 0) {
    output.innerHTML = `
      <div class="text-red-400">
        Please select files
      </div>
    `;
    return;
  }

  try {

    output.innerHTML += `
      <div class="text-indigo-300">
        Starting extraction...
      </div>
    `;

    const formData = new FormData();

    for (const file of files) {
      formData.append("files", file);
    }

    // 发请求
    const response = await fetch("http://127.0.0.1:8000/extract", {
      method: "POST",
      headers: {
        "x-api-key": apiKey
      },
      body: formData
    });

    const data = await response.json();

    if (data.success) {

      output.innerHTML += `
        <div class="text-green-400 mt-3">
          ✅ Extraction Finished
        </div>

        <div class="text-gray-300 mt-2">
          Total Reactions:
          <span class="text-indigo-300">${data.num_reactions}</span>
        </div>
      `;

    } else {

      output.innerHTML += `
        <div class="text-red-400 mt-3">
          ❌ Extraction Failed
        </div>
      `;
    }

  } catch (err) {

    output.innerHTML += `
      <div class="text-red-400 mt-3 whitespace-pre-wrap">
        ❌ ${err}
      </div>
    `;

    console.error(err);
  }
}