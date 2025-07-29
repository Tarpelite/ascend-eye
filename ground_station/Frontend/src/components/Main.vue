<template>
  <div class="dashboard-container">
    <!-- 左上角标题 -->
    <div class="header">
      <h1>无人机载荷图像实时智能感知与推理系统</h1>
      <!-- <div class="subtitle">实时飞行监控系统</div> -->
    </div>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 四个信息展示框 -->
      <div class="metrics-grid">
        <!-- 异常信息框 -->
        <el-card class="metric-card warning">
          <div class="metric-header">
            <span class="metric-icon">
              <el-icon :size="30"><Warning /></el-icon>
            </span>
            <span class="metric-title">异常信息</span>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ errorMsgCnt }}</div>
            <div class="metric-desc">最近1小时内</div>
          </div>
        </el-card>
        
        <!-- 运行时间框 -->
        <el-card class="metric-card primary">
          <div class="metric-header">
            <span class="metric-icon">
              <el-icon :size="30"><Clock /></el-icon>
            </span>
            <span class="metric-title">运行时间</span>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ runningTime }}</div>
            <div class="metric-desc">自运行以来</div>
          </div>
        </el-card>
        
        <!-- 时间框 -->
        <el-card class="metric-card info">
          <div class="metric-header">
            <span class="metric-icon">
              <el-icon :size="30"><Calendar /></el-icon>
            </span>
            <span class="metric-title">当前时间</span>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ currentTime }}</div>
            <div class="metric-desc">{{ currentDate }}</div>
          </div>
        </el-card>
        
        <!-- 天气框 -->
        <el-card class="metric-card success">
          <div class="metric-header">
            <span class="metric-icon">
              <el-icon :size="30"><Sunny /></el-icon>
            </span>
            <span class="metric-title">天气状况</span>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ weatherStatus }}</div>
            <div class="metric-desc">能见度：{{ ableDistance }}公里</div>
          </div>
        </el-card>
      </div>
      
      <!-- 飞机数量展示 -->
      <div class="aircraft-counter">
        <div class="counter-content">
          <div class="counter-label">当前监控无人机数量</div>
          <div class="counter-value">{{ droneCnt}}</div>
          <div class="counter-sub">发现异常无人机数量：{{abnormalDroneCnt}}</div>
        </div>
      </div>
      
      <!-- 模式选择按钮 -->
      <div class="mode-selector">
        <el-button 
          type="primary" 
          size="large" 
          @click="selectMode('multi')"
        >
          <el-icon class="button-icon"><Connection /></el-icon>
          <span>多机模式</span>
        </el-button>
        
        <el-button 
          type="success" 
          size="large" 
          @click="selectMode('single')"
        >
          <el-icon class="button-icon"><Position /></el-icon>
          <span>单机模式</span>
        </el-button>
      </div>
    </div>
    
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { 
  Warning, Clock, Calendar, Sunny, 
  Connection, Position,
} from '@element-plus/icons-vue';
import { getWarningData } from '../js/api';

// 当前时间和日期
const currentTime = ref('');
const currentDate = ref('');

// 更新时间函数
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
};

const errorMsgCnt = ref(3);
const runningTime = ref('00:00:00');
const weatherStatus = ref('晴朗');
const droneCnt = ref(4); 
const abnormalDroneCnt = ref(3);
const ableDistance = ref(10);

const updateAlerts = async () => {
  let totalAlerts = 0;
  const abnormalUavIds = new Set<string>();
  for (let i = 0; i < droneCnt.value; i++) {
    try {
      const res = await getWarningData(i + 1); // uav_id 从 1 开始
      if (res.warning_history && Array.isArray(res.warning_history)) {
        totalAlerts += res.warning_history.length;
        res.warning_history.forEach((item: { uav_id: string }) => {
          abnormalUavIds.add(item.uav_id);
        });
      }
    } catch (e) {
      // 可选：错误处理
    }
  }
  errorMsgCnt.value = totalAlerts;
  abnormalDroneCnt.value = abnormalUavIds.size;
};

const initBootTime = () => {
  if (!localStorage.getItem('systemBootTime')) {
    localStorage.setItem('systemBootTime', Date.now().toString());
  }
};

// 计算运行时长（时:分:秒）
const updateRunningTime = () => {
  const bootTimeStr = localStorage.getItem('systemBootTime');
  if (bootTimeStr) {
    const bootTime = Number(bootTimeStr);
    const now = Date.now();
    const diff = now - bootTime;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff / (1000 * 60)) % 60);
    const seconds = Math.floor((diff / 1000) % 60);
    runningTime.value = 
      `${hours.toString().padStart(2, '0')}:` +
      `${minutes.toString().padStart(2, '0')}:` +
      `${seconds.toString().padStart(2, '0')}`;
  } else {
    runningTime.value = '00:00:00';
  }
};

// 选择模式
const selectMode = (mode: string) => {
  if(mode === 'multi') {
    window.location.href = '/multi'; // 替换为实际的多机模式路由
    // 处理多机模式逻辑
  } else {
    window.location.href = '/single/0'; // 替换为实际的单机模式路由
    // 处理单机模式逻辑
  }
};

// 初始化定时器
let timer: number;
onMounted(async () => {
  updateTime();
  initBootTime();
  await updateAlerts();
  timer = setInterval(()=>{updateTime();updateRunningTime();}, 1000);
});

onBeforeUnmount(() => {
  clearInterval(timer);
});
</script>

<style scoped>
.dashboard-container {
  position: fixed;      /* 关键：固定定位 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  height: 100vh;        /* 视口高度 */
  width: 100vw;         /* 视口宽度 */
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  color: #fff;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  overflow: hidden;
  padding: 20px;
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
  font-size: 40px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #64b3f4, #c2e59c);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 5px;
  color: #a0d2ff;
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding-top: 60px;
}

/* 指标卡片网格布局 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 25px;
  width: 90%;
  max-width: 1000px;
  margin-bottom: 40px;
}

.metric-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  color: #fff;
  transition: all 0.3s ease;
  height: 140px;
  display: flex;
  align-items:left;
  padding: 0 25px;
  margin-top: -100px;
}

.metric-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35);
}

.metric-card.warning {
  border-left: 5px solid #ff6b6b;
}

.metric-card.primary {
  border-left: 5px solid #4dabf7;
}

.metric-card.info {
  border-left: 5px solid #20c997;
}

.metric-card.success {
  border-left: 5px solid #51cf66;
}

.metric-icon {
  margin-right: 10px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}
.metric-header {
  display: flex;
  align-items: center;
}

.metric-content {
  flex: 1;
}

.metric-title {
  font-size: 20px;
  font-weight: 600;
  opacity: 0.8;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 5px;
  letter-spacing: 1px;
}

.metric-desc {
  font-size: 14px;
  opacity: 0.7;
}

/* 飞机数量计数器 */
.aircraft-counter {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 15px;
  padding: 25px 40px;
  margin-bottom: 40px;
  width: 90%;
  max-width: 1000px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.counter-content {
  text-align: center;
}

.counter-label {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 10px;
}

.counter-value {
  font-size: 64px;
  font-weight: 800;
  background: linear-gradient(90deg, #4facfe, #00f2fe);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 5px;
  line-height: 1;
}

.counter-sub {
  font-size: 16px;
  opacity: 0.8;
}

/* 模式选择器 */
.mode-selector {
  display: flex;
  gap: 40px;
  margin-top: 20px;
}

.mode-selector .el-button {
  width: 260px;
  height: 120px;
  border-radius: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  font-size: 22px;
  font-weight: 600;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.mode-selector .el-button:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.mode-selector .el-button.active {
  border: 2px solid;
  box-shadow: 0 0 20px currentColor;
}

.mode-selector .el-button.el-button--primary {
  border-color: #4dabf7;
}

.mode-selector .el-button.el-button--primary.active {
  background: rgba(77, 171, 247, 0.15);
}

.mode-selector .el-button.el-button--success {
  border-color: #20c997;
}

.mode-selector .el-button.el-button--success.active {
  background: rgba(32, 201, 151, 0.15);
}

.button-icon {
  font-size: 36px;
  margin-bottom: 10px;
}


</style>