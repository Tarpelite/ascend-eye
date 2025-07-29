import axios from 'axios';

const instances = [5000, 5001, 5002, 5003,16532].map(port => 
  axios.create({
    baseURL: `http://localhost:${port}`,  // 添加 http:// 协议
    timeout: 50000
  })
);


export default instances;