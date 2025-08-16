
from typing import Any, Union
import asyncio
import json
import aiohttp


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fatal_error = "error" in self

    def __getattr__(self, item: str) -> Any:
        if self._fatal_error:
            raise RuntimeError(f"Cannot access attribute '{item}' because API request failed:\n{self.get('error')}")
        try:
            value = self[item]
            if isinstance(value, dict):
                return AttrDict(value)
            if isinstance(value, list):
                return [AttrDict(v) if isinstance(v, dict) else v for v in value]
            return value
        except KeyError:
            return None

    def __getitem__(self, key: Union[str, int]) -> Any:
        if self._fatal_error:
            raise RuntimeError(f"Cannot access item '{key}' because API request failed:\n{self.get('error')}")
        value = super().__getitem__(key)
        if isinstance(value, dict):
            return AttrDict(value)
        if isinstance(value, list):
            return [AttrDict(v) if isinstance(v, dict) else v for v in value]
        return value

    def __repr__(self) -> str:
        return json.dumps(self, indent=4, ensure_ascii=False)


class LiaraAPI:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://api.iran.liara.ir/v1"
        self._session: aiohttp.ClientSession | None = None
        self._own_session = False

    async def _ensure_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
            self._own_session = True

    async def close(self):
        if self._session and self._own_session:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None
            self._own_session = False

    async def __aenter__(self) -> "LiaraAPI":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> AttrDict:
        await self._ensure_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            async with self._session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientResponseError as e:
            data = {"error": f"{e.status} {e.message}", "url": url}
        except aiohttp.ClientConnectorError as e:
            data = {"error": f"Connection error: {e}", "url": url}
        except asyncio.TimeoutError:
            data = {"error": "Timeout", "url": url}
        except Exception as e:
            data = {"error": str(e), "url": url}
        return AttrDict(data)

    @staticmethod
    def _pretty_json(data: AttrDict, indent: int = 4) -> str:
        return json.dumps(data, indent=indent, ensure_ascii=False)

    #Projects
    async def list_projects(self) -> AttrDict:
        return await self._request("GET", "projects")

    async def get_project(self, project_id: str) -> AttrDict:
        return await self._request("GET", f"projects/{project_id}")

    async def create_app(
        self,
        name: str,
        plan_id: str,
        platform: str,
        read_only_fs: bool = False,
        network: str | None = None,
    ) -> AttrDict:
        data: dict[str, Any] = {
            "name": name,
            "planID": plan_id,
            "platform": platform,
            "readOnlyRootFilesystem": read_only_fs,
        }
        if network:
            data["network"] = network
        return await self._request("POST", "projects", json=data)

    async def delete_app(self, project_id: str) -> AttrDict:
        return await self._request("DELETE", f"projects/{project_id}")

    async def update_envs(
        self, project: str, variables: list[dict[str, str]]
    ) -> AttrDict:
        data = {"project": project, "variables": variables}
        return await self._request("POST", "projects/update-envs", json=data)

    #Disks
    async def list_disks(self, project_id: str) -> AttrDict:
        return await self._request("GET", f"projects/{project_id}/disks")

    async def create_disk(
        self, project_name: str, name: str, size: int
    ) -> AttrDict:
        data = {"name": name, "size": size}
        return await self._request(
            "POST", f"projects/{project_name}/disks", json=data
        )

    async def delete_disk(
        self, project_id: str, disk_name: str
    ) -> AttrDict:
        return await self._request(
            "DELETE", f"projects/{project_id}/disks/{disk_name}"
        )

    async def resize_disk(
        self, project_name: str, disk_name: str, size: int
    ) -> AttrDict:
        data = {"size": size}
        return await self._request(
            "POST", f"projects/{project_name}/disks/{disk_name}/resize", json=data
        )

    async def create_ftp(
        self, project_name: str, disk_name: str
    ) -> AttrDict:
        return await self._request(
            "POST", f"projects/{project_name}/disks/{disk_name}/ftp"
        )

    async def list_ftps(
        self, project_name: str, disk_name: str
    ) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_name}/disks/{disk_name}/ftp"
        )

    async def delete_ftp(self, ftp_name: str) -> AttrDict:
        return await self._request("DELETE", f"ftp/{ftp_name}")

    async def list_disk_backups(
        self, project_id: str, disk_name: str
    ) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_id}/disks/{disk_name}/backups"
        )

    async def create_disk_backup(
        self, project_id: str, disk_name: str
    ) -> AttrDict:
        return await self._request(
            "POST", f"projects/{project_id}/disks/{disk_name}/backups"
        )

    async def download_disk_backup(
        self, project_id: str, disk_name: str, backup_name: str
    ) -> AttrDict:
        return await self._request(
            "POST",
            f"projects/{project_id}/disks/{disk_name}/backups/{backup_name}/download",
        )

    #Domains
    async def list_domains(self) -> AttrDict:
        return await self._request("GET", "domains")

    async def create_domain(self, name: str, type_: str | None = None) -> AttrDict:
        data: dict[str, Any] = {"name": name}
        if type_:
            data["type"] = type_
        return await self._request("POST", "domains", json=data)

    async def check_domain(self, domain_id: str) -> AttrDict:
        return await self._request("GET", f"domains/{domain_id}/check")

    async def set_domain_project(self, domain_id: str, project_id: str) -> AttrDict:
        data = {"domainID": domain_id, "projectID": project_id}
        return await self._request("POST", "domains/set-project", json=data)

    async def set_domain_redirect(
        self, domain_id: str, redirect_to: str
    ) -> AttrDict:
        data = {"redirectTo": redirect_to}
        return await self._request(
            "POST", f"domains/{domain_id}/set-redirect", json=data
        )

    async def enable_ssl(self, domains: list[str]) -> AttrDict:
        data = {"domains": domains}
        return await self._request("POST", "domains/provision-ssl-certs", json=data)

    async def disable_ssl(self, domain_id: str) -> AttrDict:
        return await self._request("POST", f"domains/{domain_id}/ssl/disable")

    async def delete_domain(self, domain_id: str) -> AttrDict:
        return await self._request("DELETE", f"domains/{domain_id}")

    #Reports
    async def get_summary_report(self, project_name: str) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_name}/metrics/summary"
        )

    async def get_cpu_report(self, project_name: str) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_name}/metrics/cpu"
        )

    async def get_memory_report(self, project_name: str) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_name}/metrics/memory"
        )

    async def get_network_receive_report(self, project_name: str) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_name}/metrics/network-receive"
        )

    async def get_network_transmit_report(self, project_name: str) -> AttrDict:
        return await self._request(
            "GET", f"projects/{project_name}/metrics/network-transmit"
        )

    #Logs
    async def get_logs(self, project_name: str) -> AttrDict:
        return await self._request("GET", f"projects/{project_name}/logs")

    #Releases
    async def list_releases(self, project_name: str) -> AttrDict:
        return await self._request("GET", f"projects/{project_name}/releases")

    async def get_current_release(self, project_name: str) -> AttrDict:
        data = await self.list_releases(project_name)
        current_release_id: str | None = data.currentRelease
        if current_release_id:
            for r in data.releases or []:
                if r._id == current_release_id:
                    return r
        return AttrDict({})

    #Applets
    async def list_applets(self, project_name: str) -> AttrDict:
        return await self._request("GET", f"projects/{project_name}/applets")
