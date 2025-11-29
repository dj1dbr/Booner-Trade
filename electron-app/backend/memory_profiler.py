"""Memory Profiling Utilities für Speicherleck-Diagnose"""
import tracemalloc
import logging
import gc
from datetime import datetime
import psutil
import os

logger = logging.getLogger(__name__)

class MemoryProfiler:
    """Memory Profiling für Leak Detection"""
    
    def __init__(self):
        self.snapshots = []
        self.baseline = None
        tracemalloc.start()
        logger.info("🔍 Memory Profiler aktiviert")
    
    def take_snapshot(self, label: str = ""):
        """Nimm Memory Snapshot"""
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({
            'label': label,
            'snapshot': snapshot,
            'timestamp': datetime.now()
        })
        
        # System Memory
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        logger.info(f"📊 Memory Snapshot: {label}")
        logger.info(f"   RSS: {mem_info.rss / 1024 / 1024:.1f} MB")
        logger.info(f"   VMS: {mem_info.vms / 1024 / 1024:.1f} MB")
        
        return snapshot
    
    def compare_snapshots(self, snapshot1_label: str, snapshot2_label: str, top: int = 10):
        """Vergleiche zwei Snapshots"""
        snap1 = next((s for s in self.snapshots if s['label'] == snapshot1_label), None)
        snap2 = next((s for s in self.snapshots if s['label'] == snapshot2_label), None)
        
        if not snap1 or not snap2:
            logger.error("Snapshots nicht gefunden")
            return
        
        logger.info(f"\n📈 Memory Growth: {snapshot1_label} → {snapshot2_label}")
        
        # Vergleich
        stats = snap2['snapshot'].compare_to(snap1['snapshot'], 'lineno')
        
        logger.info(f"\nTop {top} Memory Increases:")
        for stat in stats[:top]:
            logger.info(f"{stat}")
    
    def get_top_allocations(self, top: int = 10):
        """Zeige Top Memory Allocations"""
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        logger.info(f"\n📊 Top {top} Memory Allocations:")
        for index, stat in enumerate(top_stats[:top], 1):
            logger.info(f"{index}. {stat}")
    
    def log_gc_stats(self):
        """Log Garbage Collector Stats"""
        gc.collect()
        logger.info("\n🗑️  Garbage Collector Stats:")
        logger.info(f"   Objects: {len(gc.get_objects())}")
        logger.info(f"   Garbage: {len(gc.garbage)}")
        
        # GC Counts
        counts = gc.get_count()
        logger.info(f"   Gen0: {counts[0]}, Gen1: {counts[1]}, Gen2: {counts[2]}")

# Global Instance
_profiler = None

def get_profiler():
    global _profiler
    if _profiler is None:
        _profiler = MemoryProfiler()
    return _profiler
