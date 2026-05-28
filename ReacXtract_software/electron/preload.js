const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {

  // 接收后端日志
  onBackendLog: (callback) => {
    ipcRenderer.on("backend-log", (_, data) => {
      callback(data);
    });
  },

  // 移除监听（防止重复绑定）
  removeBackendLogListeners: () => {
    ipcRenderer.removeAllListeners("backend-log");
  }

});