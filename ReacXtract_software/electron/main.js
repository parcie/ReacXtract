const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const net = require("net");

let pyProcess = null;
let manuallyClosed = false;
let crashCount = 0;
const MAX_CRASHES = 5;

const isDev = !app.isPackaged;

// 🔹 获取后端 exe 路径（开发 / 生产）
function getBackendPath() {
  if (isDev) {
    return path.join(__dirname, "../backend/dist/ReacXtract.exe");
  } else {
    // 打包后直接放在 resources 根目录
    return path.join(process.resourcesPath, "ReacXtract.exe");
  }
}

// 🔹 等待 FastAPI 端口就绪
function waitForPort(port, timeout = 15000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tryConnect = () => {
      const socket = new net.Socket();
      socket.setTimeout(1000);

      socket.once("connect", () => {
        socket.destroy();
        resolve();
      });

      socket.once("error", () => {
        socket.destroy();
        if (Date.now() - start > timeout) {
          reject(new Error("Backend startup timeout"));
        } else {
          setTimeout(tryConnect, 500);
        }
      });

      socket.connect(port, "127.0.0.1");
    };
    tryConnect();
  });
}

// 🔹 启动后台 exe
function startBackend() {
  const backendPath = getBackendPath();

  console.log(`🚀 启动后端服务: ${backendPath}`);

  pyProcess = spawn(backendPath, [], {
    cwd: path.dirname(backendPath),
    windowsHide: true,
    detached: true,
    stdio: ["pipe", "pipe", "pipe"]
  });

  pyProcess.unref();

  pyProcess.stdout.on("data", (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  pyProcess.stderr.on("data", (data) => {
    console.error(`[Backend Error] ${data.toString().trim()}`);
  });

  pyProcess.on("close", (code) => {
    console.log(`后端进程退出，退出码: ${code}`);
    pyProcess = null;
    if (!manuallyClosed && crashCount < MAX_CRASHES) {
      crashCount++;
      console.log(`⚠️  后端崩溃，正在重启... (${crashCount}/${MAX_CRASHES})`);
      setTimeout(startBackend, 1500);
    }
  });

  pyProcess.on("error", (err) => {
    console.error("❌ 启动后端失败:", err);
  });
}

// 🔹 创建主窗口
async function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      enableRemoteModule: false
    },
    icon: path.join(__dirname, "assets/icon.ico") // 如果有图标可添加
  });

  await win.loadFile(path.join(__dirname, "index.html"));

  if (isDev) {
    win.webContents.openDevTools();
  }

  win.webContents.on('did-finish-load', () => {
    console.log("✅ Electron 前端界面加载完成");
    console.log("📡 后端接口地址: http://127.0.0.1:8000/extract");
  });

  win.on("close", () => {
    manuallyClosed = true;
  });
}

// 🔹 主流程
async function main() {
  console.log("=== ReacXtract 启动中 ===");

  startBackend();

  try {
    await waitForPort(8000, 20000);  // 增加超时时间
    console.log("✅ 后端服务已就绪");
    await createWindow();
  } catch (err) {
    console.error("❌ 启动失败:", err);
    app.quit();
  }
}

app.whenReady().then(main);

app.on("before-quit", () => {
  manuallyClosed = true;
  if (pyProcess) {
    console.log("🛑 正在关闭后端服务...");
    try {
      pyProcess.kill();
    } catch (e) {}
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});