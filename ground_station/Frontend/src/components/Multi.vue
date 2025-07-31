<template>
  <div>
    <div class="dashboard-container">
      <!-- 左上角标题 -->
      <div class="header">
        <h1><span @click="$router.push('/main')">无人机载荷图像实时智能感知与推理系统</span>-机群控制模式</h1>
      </div>
      
      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 左侧无人机选择面板 -->
        <div class="drone-selector">
          <el-card class="selector-card">
            <div class="selector-header">
              <el-icon :size="28"><Position /></el-icon>
              <span>无人机选择</span>
            </div>
            
            <div 
              v-for="(drone, index) in drones" 
              :key="index"
              class="drone-item"
              :class="{ 'active': selectedDrone.id === drone.id }"
              @click="selectDrone(drone)"
            >
              <div class="drone-icon">
                <el-icon :size="32"><Connection /></el-icon>
              </div>
              <div class="drone-info">
                <div class="drone-name">{{ drone.name }}</div>
                <div>
                  <span class="drone-status" :class="drone.inonline">
                    {{ drone.inonline === 'normal' ? '在线' : '离线' }}
                  </span>
                  <span class="drone-status" :class="drone.status">
                    {{ drone.status === 'normal' ? '正常' : '发现异常' }}
                  </span>
                </div>
                
              </div>
              <!-- 跳转按钮，放在右侧 -->
              <el-button
                type="primary"
                plain
                size="medium"
                class="drone-jump-btn"
                @click="handleJump(index)"
              >
              <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </el-card>
          
          <!-- 无人机状态摘要 -->
          <el-card class="status-summary">
            <div class="summary-item">
              <span>总无人机数</span>
              <span class="value">{{ drones.length }}</span>
            </div>
            <div class="summary-item">
              <span>在线无人机</span>
              <span class="value">{{ onlineDrones }}</span>
            </div>
            <div class="summary-item">
              <span>异常无人机</span>
              <span class="value error">{{ abnormalDrones }}</span>
            </div>
          </el-card>
        </div>
        
        <!-- 中间视频流区域 -->
        <div class="video-container">
          <!-- <div class="video-header">
            <div class="video-title">
              <el-icon><VideoCamera /></el-icon>
              <span>{{ selectedDrone.name }} - 实时视频流</span>
            </div>
          </div> -->
          
          <!-- 视频流显示 -->
          <div class="video-display">
            <div class="video-grid-container">
              <div class="video-grid">
                <div
                  v-for="drone in drones"
                  :key="drone.id"
                  class="video-grid-item"
                >
                  <div class="video-title">
                    <el-icon><VideoCamera /></el-icon>
                    <span>{{ drone.name }} - 实时视频流</span>
                  </div>
                  <img
                    v-if = 'drone.inonline === "normal"'
                    :src="drone.videoUrl"
                    alt="无人机实时视频流"
                    class="video-grid-stream"
                  />
                  <div v-else>
                    <el-icon style="font-size:48px;color:#ff6b6b;"><Warning /></el-icon>
                    <div style="color:#ff6b6b;margin-top:8px;">无人机未连接</div>
                  </div>
                </div>
              </div>
            </div>
            
            
          </div>
        </div>
        
        <!-- 右侧异常信息面板 -->
        <div class="alert-panel">
          <el-card class="alert-card">
            <div class="alert-header">
              <el-icon :size="28"><Warning /></el-icon>
              <span>实时异常信息</span>
              <el-button type="info" class="alert-count" @click="historyDialogVisible=true" plain>历史信息</el-button>
            </div>
            
            <div class="alert-list-container">
              <div class="alert-list">
                <div
                  v-for="(alert, idx) in alerts"
                  :key="idx"
                  class="alert-item"
                  @click="showAlertDialog(alert)"
                >
                  <div>
                    <strong>无人机：</strong>{{ alert.uav_id }}
                    <strong>时间：</strong>{{ alert.time }}
                  </div>
                  <div>
                    <strong>警告：</strong>{{ alert.alert }}
                  </div>
                  <div>
                    <a
                      :href="`http://localhost:16532/${alert.video_file_name}`"
                      target="_blank"
                      rel="noopener"
                    >查看视频</a>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
    <!-- 弹窗部分也要放在这个div内 -->
    <el-dialog 
      v-model="historyDialogVisible" 
      title="历史记录" 
      width="80%"
      top="5vh"
      class="history-dialog"
    >
      <div class="history-container">
        <el-table :data="historyAlerts" style="background-color: transparent; height: 100%;">
          <el-table-column prop="time" label="时间" width="120" />
          <el-table-column prop="title" label="事件标题" width="200" />
          <el-table-column prop="drone" label="关联无人机" width="150" />
          <el-table-column prop="info" label="信息" />
        </el-table>
      </div>
    </el-dialog>
    <el-dialog 
      v-model="alertDialogVisible" 
      width="70%"
      center
      custom-class="alert-detail-dialog"
    >
      <div class="alert-detail-container">
        <div class="alert-image">
          <canvas
            ref="bboxCanvas"
            class="bbox-canvas"
            :style="{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none'
          }"
          />
          <img
            :src="`http://localhost:16532/${currentAlert.picture_file_name}`"
            ref="alertImg"
            class="alert-img-full"
            @load="drawBboxes"
          />
        </div>
        <div class="alert-content">
          <div class="alert-meta">
            <div class="meta-item">
              <!-- <el-icon><Clock /></el-icon> -->
              <div>时间</div>
              <span>{{ currentAlert.time }}</span>
            </div>
            <!-- <div class="meta-item">
              <el-icon><Connection /></el-icon>
              <span>无人机: {{ currentAlert.uav_id || '未知' }}</span>
            </div> -->
          </div>
          <div class="alert-description">
            <h3>事件详情</h3>
            <div class="description-content-wrapper">
              <div class="description-content" v-html="highlightedDescription" 
                   @mouseover="handleMouseEnter" 
                   @mouseout="handleMouseLeave"></div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount,watch,nextTick, computed } from 'vue';
import { 
  Warning, Position, Connection, 
  VideoCamera, ArrowRight
} from '@element-plus/icons-vue';
import { getDroneData,getHistoryData,getWarningData } from '../js/api';

// 无人机数据
const drones = ref([
  { id: 0, name: '侦察无人机-01', inonline:'abnormal',status: 'normal', location: '东经116.4°, 北纬39.9°', altitude: 1200, videoUrl: 'http://localhost:5000/video_feed' },
  { id: 1, name: '测绘无人机-02', inonline:'abnormal',status: 'normal', location: '东经116.5°, 北纬39.8°', altitude: 800,videoUrl: 'http://localhost:5001/video_feed' },
  { id: 2, name: '应急无人机-03', inonline:'abnormal',status: 'normal', location: '东经116.3°, 北纬40.0°', altitude: 1500, videoUrl: 'http://localhost:5002/video_feed' },
  { id: 3, name: '巡逻无人机-04', inonline:'abnormal',status: 'normal', location: '东经116.6°, 北纬39.7°', altitude: 600, videoUrl: 'http://localhost:5003/video_feed' }
]);
const selectedDrone = ref(drones.value[0]);

const droneAllFrames = ref<any[][]>([[], [], [], []]); // 4个无人机，每个是帧数组
const droneFrameIndex = ref([0, 0, 0, 0]); // 当前帧索引
const currentDroneFrame = ref<any>({
  longitude: 0,
  latitude: 0,
  altitude: 0,
  vx: 0,
  vy: 0,
  vz: 0
});

// 获取所有无人机的所有帧数据
const fetchAllDroneFrames = async () => {
  for (let i = 0; i < 4; i++) {
    try {
      const res = await getDroneData(i);
      droneAllFrames.value[i] = res.data || [];
      droneFrameIndex.value[i] = 0;
    } catch (e) { 
      droneAllFrames.value[i] = [];
    }
  }
  updateCurrentDroneFrame();
};

// 每秒切换当前无人机的帧
const updateCurrentDroneFrame = () => {
  const idx = drones.value.findIndex(d => d.id === selectedDrone.value.id);
  const frames = droneAllFrames.value[idx] || [];
  if (frames.length > 0) {
    currentDroneFrame.value = frames[droneFrameIndex.value[idx]];
    droneFrameIndex.value[idx] = (droneFrameIndex.value[idx] + 1) % frames.length;
  } else {
    currentDroneFrame.value = {
      longitude: 0,
      latitude: 0,
      altitude: 0,
      vx: 0,vy: 0,vz: 0
    };
  }
};

// 切换无人机时立即切换帧
watch(selectedDrone, () => {
  updateCurrentDroneFrame();
});

// 定时器
let droneFrameTimer: number;

// 选中的无人机


// 视频流URL
const videoUrl = ref('');

// 视频流统计信息

// 异常信息
const alerts = ref<Array<{
  uav_id: string;
  time: string;
  alert: string;
  video_file_name: string;
  picture_file_name: string;
  label_img_name: string;
  label_json_name: string;
  description: string;
  bboxes: Array<{ class: string; bbox: number[] }>;
  mapping: Record<string, string[]>;
}>>([]);

const updateAlerts = async () => {
  alerts.value.length = 0; // 清空原有内容
  for (let i = 0; i < 4; i++) {
    try {
      const res = await getWarningData(i+1); // uav_id 从 1 开始
      console.log('异常数据',res)
      if (res.warning_history && Array.isArray(res.warning_history)) {
        res.warning_history.forEach((item: { uav_id: string; time: string; info: any }) => {
          alerts.value.push({
            uav_id: item.uav_id,
            time: item.time,
            ...item.info // 展开 info 里的所有内容
          });
        });
      }
    } catch (e) {
      // 可选：错误处理
    }
  }
  const abnormalUavIds = new Set(alerts.value.map(a => String(a.uav_id)));

// 更新 drones 状态
  drones.value.forEach(drone => {
    if (abnormalUavIds.has(String(drone.id+1))) {
      drone.status = 'abnormal'; // 或 '异常'
    } else {
      drone.status = 'normal'; // 或 '正常'
    }
  });

  // 统计异常无人机数量
  abnormalDrones.value = abnormalUavIds.size;
};


// 当前时间
const currentTime = ref('');
const currentDate = ref('');
const lastUpdateTime = ref('');

// 统计信息
const onlineDrones = ref(0);
const abnormalDrones = ref(1);

// 历史信息展示
const historyDialogVisible = ref(false);
const historyAlerts = ref([
  { time: '14:00:00', title: '无人机-01异常', drone: '侦察无人机-01', location: '东经116.4°, 北纬39.9°', level: 'critical',info:'' },
  { time: '13:55:00', title: '无人机-02异常', drone: '测绘无人机-02', location: '东经116.5°, 北纬39.8°', level: 'warning',info:'' },
  { time: '13:50:00', title: '无人机-03异常', drone: '应急无人机-03', location: '东经116.3°, 北纬40.0°', level: 'critical',info:'' },
  { time: '13:45:00', title: '无人机-04异常', drone: '巡逻无人机-04', location: '东经116.6°, 北纬39.7°', level: 'warning',info:'' }
]);

const updateHistory = async()=>{
  const allHistory: any[] = [];
  for (let i = 0; i < 4; i++) {
    try {
      const res = await getHistoryData(i+1); // uav_id 从 1 开始
      if (res.history && Array.isArray(res.history)) {
        res.history.forEach((item:{uav_id:string;time:string;info:string}) => {
          allHistory.push({
            time: item.time,
            title: `无人机-${item.uav_id}历史`,
            drone:`无人机-${item.uav_id}`,
            info: item.info
          });
        });
      }
    } catch (e) {
      // 可选：错误处理
    }
  }
  historyAlerts.value = allHistory;
}


// 异常信息弹窗
const alertDialogVisible = ref(false);
const currentAlert = ref<{
  uav_id: string;
  time: string;
  alert: string;
  video_file_name: string;
  picture_file_name: string;
  label_img_name: string;
  label_json_name: string;
  description: string; 
  bboxes: Array<{ class: string; bbox: number[] }>;
  mapping: Record<string, string[]>;
}>({
  uav_id: '',
  time: '',
  alert: '',
  video_file_name: '',
  picture_file_name: '',
  label_img_name: '',
  label_json_name: '',
  description: '',
  bboxes: [],
  mapping: {}
});
const showAlertDialog = (alert: any) => {
  currentAlert.value = alert;
  alertDialogVisible.value = true;
  
  // 等待DOM更新后初始化画布
  nextTick(() => {
    const img = alertImg.value;
    const canvas = bboxCanvas.value;
    if (img && canvas) {
      // 初始化时不绘制任何标注框
      activeKey.value = '';
      drawBboxes();
    }
  });
};

const alertImg = ref<HTMLImageElement | null>(null);
const bboxCanvas = ref<HTMLCanvasElement | null>(null);
const imgWidth = ref(0);
const imgHeight = ref(0);
const activeKey = ref('');

// 计算高亮的事件描述
const highlightedDescription = computed(() => {
  if (!currentAlert.value.description) return '无详细描述';
  
  let description = currentAlert.value.description;
  const mapping = currentAlert.value.mapping || {};
  
  // 为每个mapping中的类别创建高亮标记
  Object.keys(mapping).forEach(key => {
    const regex = new RegExp(key, 'g');
    description = description.replace(regex, 
      `<span class="highlightable-text" data-key="${key}">${key}</span>`
    );
  });
  
  return description;
});

// 处理鼠标悬停事件
const handleMouseEnter = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  console.log('Mouse enter target:', target);
  if (target.classList.contains('highlightable-text')) {
    const key = target.dataset.key || '';
    console.log('Setting active key to:', key);
    setActiveKey(key);
  }
};

const handleMouseLeave = () => {
  setActiveKey('');
};

// 画框
const drawBboxes = () => {
  if (!bboxCanvas.value || !currentAlert.value) {
    console.log('Canvas or currentAlert not available');
    return;
  }
  
  const ctx = bboxCanvas.value.getContext('2d');
  if (!ctx) {
    console.log('Canvas context not available');
    return;
  }
  
  const img = alertImg.value;
  if (!img) {
    console.log('Alert image not available');
    return;
  }
  
  // 确保画布尺寸与图片显示尺寸一致
  const imgRect = img.getBoundingClientRect();
  bboxCanvas.value.width = imgRect.width;
  bboxCanvas.value.height = imgRect.height;
  
  console.log('Canvas size:', bboxCanvas.value.width, 'x', bboxCanvas.value.height);
  console.log('Image rect size:', imgRect.width, 'x', imgRect.height);
  console.log('Image natural size:', img.naturalWidth, 'x', img.naturalHeight);
  
  // 清除画布
  ctx.clearRect(0, 0, bboxCanvas.value.width, bboxCanvas.value.height);
  
  // 如果没有激活的类别，不绘制任何标注框
  if (!activeKey.value) {
    console.log('No active key, not drawing boxes');
    return;
  }
  
  const bboxes = Array.isArray(currentAlert.value.bboxes) ? currentAlert.value.bboxes : [];
  console.log('Active key:', activeKey.value, 'Bboxes:', bboxes);
  
  // 计算缩放比例 - 使用图片的实际显示尺寸
  const scaleX = imgRect.width / img.naturalWidth;
  const scaleY = imgRect.height / img.naturalHeight;
  
  bboxes.forEach((box) => {
    // 只绘制与当前激活类别匹配的标注框
    if (box.class === activeKey.value) {
      console.log('Drawing box for class:', box.class, 'bbox:', box.bbox);
      const [x1, y1, x2, y2] = box.bbox;
      
      // 缩放坐标
      const scaledX1 = x1 * scaleX;
      const scaledY1 = y1 * scaleY;
      const scaledX2 = x2 * scaleX;
      const scaledY2 = y2 * scaleY;
      
      const w = scaledX2 - scaledX1;
      const h = scaledY2 - scaledY1;
      
      console.log('Scaled coordinates:', { scaledX1, scaledY1, w, h });
      
      // 绘制高亮标注框
      ctx.strokeStyle = '#00FF00';
      ctx.lineWidth = 3;
      ctx.strokeRect(scaledX1, scaledY1, w, h);
      
      // 绘制文字背景
      ctx.font = '18px Arial';
      const textWidth = ctx.measureText(box.class).width;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(scaledX1 + 4, scaledY1 - 20, textWidth + 8, 20);
      
      // 绘制文字
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 3;
      ctx.strokeText(box.class, scaledX1 + 4, scaledY1 - 5);
      ctx.fillStyle = '#00FF00';
      ctx.fillText(box.class, scaledX1 + 4, scaledY1 - 5);
    }
  });
};

// 高亮逻辑
const setActiveKey = (key: string) => {
  activeKey.value = key;
  drawBboxes();
};



// 更新时间
const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  });
  currentDate.value = now.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
  });
  lastUpdateTime.value = now.toLocaleTimeString('zh-CN');
};



// 选择无人机
const selectDrone = (drone: any) => {
  selectedDrone.value = drone;
  videoUrl.value = drone.videoUrl;
  
  // 添加随机参数确保刷新
  const timestamp = new Date().getTime();
  videoUrl.value = `${drone.videoUrl}?t=${timestamp}`;
};

// 处理无人机跳转
const handleJump = (index: number) => {
  // 这里可以自定义跳转逻辑，比如跳转到详情页
  // 例如：window.location.href = `/drone/${drones.value[index].id}`;
  // 或用路由跳转：router.push(`/drone/${drones.value[index].id}`);
  window.location.href = `/single/${index}`;
};

// 更新视频统计信息

// 初始化WebSocket连接
let ws: WebSocket | null = null;
const initWebSocket = () => {
  if (ws) {
    ws.close();
  }
  ws = new WebSocket('ws://localhost:16532/alerts');
  ws.onopen = () => {
    console.log('WebSocket 连接已建立');
  };
  ws.onmessage = async () => {
    // 每次收到消息，刷新异常和历史信息
    await updateAlerts();
    await updateHistory();
  };
  ws.onerror = (err) => {
    console.error('WebSocket 发生错误:', err);
  };
  ws.onclose = () => {
    console.log('WebSocket 连接已关闭');
    // 可选：自动重连
    setTimeout(initWebSocket, 3000);
  };
};
const checkDroneOnline=(drone: { videoUrl: string }, callback: (online: boolean) => void)=>{
  const img = new Image();
  let timer: number | null = null;

  img.onload = () => {
    if (timer) clearTimeout(timer);
    callback(true); // 能加载到图片，认为在线
  };
  img.onerror = () => {
    if (timer) clearTimeout(timer);
    callback(false); // 加载失败，认为离线
  };
  // 超时处理（如3秒无响应认为离线）
  timer = window.setTimeout(() => {
    img.src = ''; // 取消加载
    callback(false);
  }, 3000);

  img.src = drone.videoUrl + '?t=' + Date.now(); // 加时间戳防缓存
}

// 初始化定时器
let timer: number;
onMounted(async () => {
  await fetchAllDroneFrames();
  await updateHistory();
  await updateAlerts();
  drones.value.forEach((drone) => { 
    checkDroneOnline(drone, (online) => {
      drone.inonline = online ? 'normal' : 'abnormal';
      if(online) onlineDrones.value++;
    });
  });
  selectDrone(drones.value[0]); // 默认选择第一个无人机
  droneFrameTimer = setInterval(updateCurrentDroneFrame, 1000);
  updateTime();
  timer = setInterval(updateTime, 1000);
  initWebSocket();
});

onBeforeUnmount(() => {
  clearInterval(timer);
  clearInterval(droneFrameTimer);
  if (ws) {
    ws.close();
    ws = null;
  }
});
</script>

<style>
.dashboard-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  height: 100%;
  width: 100vw;
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  color: #fff;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  overflow: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  z-index: 0;
}

/* 左上角标题样式 */
.header {
  position: absolute;
  top: 20px;
  left: 30px;
  z-index: 10;
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #64b3f4, #c2e59c);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex: 1;
  min-height: 0;
  margin-top: 60px;
  gap: 20px;
  padding: 0 20px;
}

/* 左侧无人机选择面板 */
.drone-selector {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 60px;
}

.selector-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: none;
  color: #fff;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.drone-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.drone-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
}

.drone-item:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(5px);
}

.drone-item.active {
  background: rgba(77, 171, 247, 0.2);
  border-left: 3px solid #4dabf7;
}

.drone-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}

.drone-info {
  flex: 1;
}

.drone-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.drone-status {
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
}

.drone-status.normal {
  background: rgba(32, 201, 151, 0.2);
  color: #20c997;
}

.drone-status.abnormal {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
}
.drone-jump-btn {
  margin-left: auto;
  padding: 6px 12px;
  font-size: 14px;
  color: #fff;
  background-color: transparent;
  border-color: transparent;
  border-radius: 8px;
}

.status-summary {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: none;
  color: #fff;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item .value {
  font-weight: 700;
  color: #4facfe;
}

.summary-item .error {
  color: #ff6b6b;
}

/* 中间视频流区域 */
.video-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 0 10px;
}

.video-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.video-stats {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #a0d2ff;
}

.video-display {
  flex: 1;
  background: rgba(0, 0, 0, 0);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  margin-top: 50px;
}

.video-stream {
  width: 100%;
  height: auto;
  object-fit: cover;
}

.video-osd {
  position: absolute;
  bottom: 20px;
  left: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(0, 0, 0, 0.6);
  padding: 12px 20px;
  border-radius: 8px;
}

.osd-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

/* 右侧异常信息面板 */
.alert-panel {
  width: 380px;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* ✅ 必加 */
  margin-top: -50px;
}

.alert-card {
  flex: 1; /* ✅ 一定要有 */
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* ✅ 避免外部滚动冲突 */
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: none;
  color: #fff;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0; /* 防止标题区域收缩 */
}

.alert-count {
  margin-left: auto;
}

/* 新增滚动容器 */
.alert-list-container {
  height: 100dvh;
  overflow-y: auto;
}

.alert-list {
  flex: 1;
  padding-right: 5px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.alert-item {
  padding: 15px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  border-left: 3px solid;
  flex-shrink: 0; /* 防止项目被压缩 */
}

.alert-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.alert-item.critical {
  border-left-color: #ff6b6b;
}

.alert-item.warning {
  border-left-color: #ffc53d;
}

.alert-item.info {
  border-left-color: #4dabf7;
}

.alert-time {
  font-size: 12px;
  color: #a0d2ff;
  margin-bottom: 8px;
}

.alert-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 5px;
}

.alert-title .critical {
  color: #ff6b6b;
}

.alert-title .warning {
  color: #ffc53d;
}

.alert-desc {
  font-size: 14px;
  color: #ccc;
  margin-bottom: 10px;
  line-height: 1.4;
}

.alert-location {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #a0d2ff;
}

/* 滚动条样式 */
.alert-list-container::-webkit-scrollbar {
  width: 8px;
}

.alert-list-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.alert-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 1);
  border-radius: 4px;
}

.alert-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
.alert-detail-dialog {
  background: rgba(232, 232, 232, 0.95);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.alert-detail-container {
  display: flex;
  gap: 20px;
  height: 60vh;
}

.alert-image {
  position: relative;
  display: inline-block;
  line-height: 0;
}

.alert-image img {
  height: 60vh;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  /* padding: px; */
  margin-left: -8px;
}

.alert-meta {
  /* display: grid; */
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  background: rgba(184, 184, 184, 0.3);
  padding: 15px;
  border-radius: 8px;
}

.meta-item {
  /* display: flex; */
  /* align-items: center; */
  gap: 1px;
  font-size: 14px;
}

.alert-description, .alert-analysis {
  background: rgba(185, 185, 185, 0.3);
  padding: 2px;
  border-radius: 5px;
}

.alert-description h3, .alert-analysis h3 {
  color: #64b3f4;
  font: 600 18px 'Segoe UI', sans-serif;
  margin-top: 5px;
  margin-bottom: 5px;
}
.alert-description p, .alert-analysis p {
  color: #333;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.6;
}

.alert-actions {
  display: flex;
  gap: 15px;
  margin-top: auto;
}

/* 弹窗样式 */
.history-dialog {
  background: rgba(255, 255, 255, 1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}
.history-container {
  display: flex; 
  flex-direction: column;
  height: 80vh; /* 增加高度从70vh到80vh */
  background-color: transparent;
  width: 100%; /* 确保宽度占满 */
}

.history-pagination {
  display: flex;
  justify-content: center;
  padding: 15px 0;
  margin-top: 10px;
  background-color: transparent;
}


.bbox-canvas {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
}
.desc-item {
  padding: 4px 0;
  transition: background 0.2s;
}
.desc-item.active {
  background: rgba(255, 107, 107, 0.15);
  color: #ff6b6b;
}
/* 高亮文本样式 */
.highlightable-text {
  color: #4facfe;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 4px;
}

.highlightable-text:hover {
  background: rgba(79, 172, 254, 0.2);
  color: #ff6b6b;
}

.description-content-wrapper {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  /* padding: 0px; */
  background: rgba(255, 255, 255, 0.8);
}

.description-content {
  line-height: 1.6;
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

/* 滚动条样式 */
.description-content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.description-content-wrapper::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.description-content-wrapper::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.description-content-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
.video-grid-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.video-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 30px;
  width: 100%;
  height: 80vh;
}

.video-grid-item {
  background: rgba(0,0,0,0.7);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 0;
  min-width: 0;
}

.video-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
}
.video-grid-stream {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 改为cover */
  border-radius: 8px;
  background: #222;
  display: block;
  max-width: 100%;
  max-height: 100%;
}
.video-grid-error {
  width: 100%;
  height: 100%;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #222;
  border-radius: 8px;
}
/* canvas {
  background-color:#0f2027;
} */
/* 响应式调整 */
@media (max-width: 1200px) {
  .drone-selector {
    width: 250px;
  }
  
  .alert-panel {
    width: 320px;
  }
}
</style>