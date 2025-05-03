import logging

class CacheManager:
    def __init__(self):
        self.logger = logging.getLogger("shoestring.cache_manager")
        self.logger.debug({"event": "cache_manager_init"})

    def is_image_cached(self, image_ref):
        self.logger.info({
            "event": "is_image_cached_called",
            "image_ref": image_ref
        })
        self.logger.debug(f"[skeleton] Would check if image cached: {image_ref}")
        return False

    def pull_image(self, image_ref):
        self.logger.info({
            "event": "pull_image_called",
            "image_ref": image_ref
        })
        self.logger.debug(f"[skeleton] Would pull image: {image_ref}")
        return True 