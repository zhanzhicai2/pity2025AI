"""
服务器监控路由
"""

from fastapi import APIRouter, Depends, Query

from app.handler.fatcory import PityResponse
from app.routers.monitor.service import ServerMonitorService
from app.routers import Permission

router = APIRouter(prefix='/monitor', tags=['系统监控'])


@router.get("/server/info")
async def get_server_monitor_info(user_info: dict = Depends(Permission())):
    """获取服务器完整监控信息"""
    monitor_data = ServerMonitorService.get_monitor_data()
    return PityResponse.success(monitor_data.model_dump())


@router.get("/server/cpu")
async def get_cpu_info(user_info: dict = Depends(Permission())):
    """获取CPU信息"""
    cpu_info = ServerMonitorService.get_cpu_info()
    return PityResponse.success(cpu_info.model_dump())


@router.get("/server/memory")
async def get_memory_info(user_info: dict = Depends(Permission())):
    """获取内存信息"""
    memory_info = ServerMonitorService.get_memory_info()
    return PityResponse.success(memory_info.model_dump())


@router.get("/server/disk")
async def get_disk_info(user_info: dict = Depends(Permission())):
    """获取磁盘信息"""
    disk_info = ServerMonitorService.get_disk_info()
    return PityResponse.success([d.model_dump() for d in disk_info])


@router.get("/server/network")
async def get_network_info(user_info: dict = Depends(Permission())):
    """获取网络信息"""
    network_info = ServerMonitorService.get_network_info()
    return PityResponse.success([n.model_dump() for n in network_info])


@router.get("/server/processes")
async def get_processes_info(
    limit: int = Query(10, ge=1, le=100),
    user_info: dict = Depends(Permission())
):
    """获取占用资源最多的进程"""
    processes = ServerMonitorService.get_top_processes(limit)
    return PityResponse.success([p.model_dump() for p in processes])
