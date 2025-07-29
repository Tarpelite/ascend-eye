<template>
    <div class="container">
    <!-- Logo部分 -->
    <div class="logo-container">
      <img 
        src="../../assets/image.png"
        alt="App Logo"
        class="logo"
      />
    </div>
    
    <!-- 标题 -->
    <h1 class="title">无人机载荷图像实时智能感知与推理系统</h1>
    
    <!-- 密码输入框 -->
    <el-input
      v-model="inputPassword"
      placeholder="请输入密码"
      show-password
      clearable
      @keyup.enter="handleLogin"
      class="password-input"
    />
    
    <!-- 登录按钮 -->
    <el-button
      type="primary"
      @click="handleLogin"
      class="login-btn"
    >
      进入系统
    </el-button>
  </div>
</template>

<script setup lang="ts">
    import { ref } from 'vue';
    import {ElMessage} from 'element-plus';
    import 'element-plus/theme-chalk/el-input.css';

    const password = ref('123456');
    const inputPassword = ref('');

    const handleLogin = ref(()=>{
        if(inputPassword.value === password.value){
            // 密码正确，跳转到主页面
            window.location.href = '/main'; // 替换为实际的主页面路由
        } else {
            // 密码错误，提示用户
            ElMessage({
              message: '密码错误，请重新输入',
              type: 'error',
              duration: 2000
            }); 
        }
    })
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: #ffffff;
  padding: 20px;
  margin-top: -110px; /* 调整顶部间距 */
}

.logo-container {
  margin-bottom: 30px;
}

.logo {
  width: 120px;
  height: 120px;
  object-fit: contain;
}

.title {
  color: #303133;
  margin-bottom: 30px;
  font-size: 40px;
  font-weight: bold;
}

.password-input {
  width: 300px;
  margin-bottom: 20px;
}

.login-btn {
  width: 300px;
  height: 40px;
  background-color: #303133;
  border-color: #303133;
}
</style>