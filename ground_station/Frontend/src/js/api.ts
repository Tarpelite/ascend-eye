import instances from  "./axios";

export const getDroneData = async(droneId:number)=> {
    try{
        const res = await instances[droneId].get('/uav_data');
        if(res.status !== 200) {
            throw new Error('获取无人机信息失败');
        }
        return res.data;
    }catch (error) {
        console.error('Error fetching drone data:', error);
        throw error;
    }
}
export const getHistoryData = async(droneId:number)=>{
    try{
        const res = await instances[4].get('/history/'+droneId);
        if(res.status !== 200) {
            throw new Error('获取历史信息失败');
        }
        return res.data;
    }catch (error) {
        console.error('Error fetching drone data:', error);
        throw error;
    }
}
export const getWarningData = async(droneId:number)=>{
    try{
        const res = await instances[4].get('/warning_history/'+droneId);
        if(res.status !== 200) {
            throw new Error('获取预警信息失败');
        }
        return res.data;
    }catch (error) {
        console.error('Error fetching warning data:', error);
        throw error;
    }
}

export const getIRVideoUrl = (droneId: number): string => {
    // 根据无人机ID生成红外视频流URL
    const port = 5000 + droneId;
    return `http://localhost:${port}/IR_feed`;
}