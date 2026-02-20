# AzerothCore Dev-Server Development Guide

This guide documents the development workflow for modifying AzerothCore modules using the Docker dev-server environment.

---

## Quick Reference

### CRITICAL: Docker Timestamp Issue

Windows Docker has a timestamp sync issue - files edited on Windows don't update timestamps inside the container, so `make` doesn't detect changes. **You MUST touch files inside the container before compiling.**

### Pre-Flight: Verify Docker is Healthy

**Always run this before starting any compilation.** If Docker Desktop was restarted or is unresponsive, compilation will hang indefinitely.

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 echo 'Docker OK'"
```

Expected output: `Docker OK`. If this times out or errors, check Docker Desktop.

### Incremental Build (manual steps required)

```powershell
# Step 1: Stop worldserver
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 pkill -9 worldserver"

# Step 2: Touch ONLY the changed module's source files
# !!! NEVER touch files in other modules (e.g. mod-playerbots) !!!
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'find /azerothcore/modules/mod-llm-chatter/src -name \"*.cpp\" -o -name \"*.h\" | xargs touch'"

# Step 3: Compile modules
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make -j12 modules 2>&1'"

# Step 4: Link worldserver
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make -j12 worldserver 2>&1'"

# Step 5: Install binary + fix permissions
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make install 2>&1 && chmod +x /azerothcore/env/dist/bin/worldserver'"

# Step 6: Restart container
docker compose --profile dev restart ac-dev-server
```

### Full Rebuild (new modules or CMakeLists changes, ~2 hours)

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && cmake /azerothcore -DCMAKE_INSTALL_PREFIX=/azerothcore/env/dist -DAPPS_BUILD=world-only -DTOOLS_BUILD=none -DSCRIPTS=static -DMODULES=static 2>&1 && make -j12 2>&1 && make install 2>&1 && chmod +x /azerothcore/env/dist/bin/worldserver'"
```

### Other Commands

```bash
# Restart Python bridges (for Python-only changes)
docker restart ac-llm-guide-bridge
docker restart ac-llm-chatter-bridge

# Backup database
docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/backup-database.sh
```

**Important:** Use PowerShell for docker commands that need output (see Troubleshooting section).

---

## Filesystem Architecture

Understanding where files live is critical for proper compilation.

### Mount Hierarchy

```
Windows Host                          Docker Container
─────────────────────────────────────────────────────────────────
C:\azerothcore-wotlk\  ──bind mount──>  /azerothcore/
    ├── src/                              ├── src/           (Windows)
    ├── modules/                          ├── modules/       (Windows)
    ├── env/dist/bin/                     ├── env/dist/bin/  (Windows) ← FINAL BINARIES
    ├── env/dist/etc/                     ├── env/dist/etc/  (Windows) ← CONFIGS
    └── var/build/     ──shadowed by──>   └── var/build/     (Docker volume)
    └── var/ccache/    ──shadowed by──>   └── var/ccache/    (Docker volume)
```

### What This Means

| Path | Storage | Visible on Windows? | Purpose |
|------|---------|---------------------|---------|
| `src/`, `modules/` | Windows NTFS | Yes | Source code you edit |
| `env/dist/bin/` | Windows NTFS | Yes | Final binaries (worldserver, authserver) |
| `env/dist/etc/` | Windows NTFS | Yes | Config files |
| `var/build/obj/` | Docker volume | No | Intermediate .o files |
| `var/ccache/` | Docker volume | No | Compiler cache |

**Why Docker volumes for build?** Compiling on Windows NTFS is 3-5x slower. Docker volumes use native Linux ext4 filesystem inside WSL2 for much better performance.

**Key insight:** When you delete Docker volumes, the **binaries on Windows persist**. For a true clean build, you must delete binaries from `env/dist/bin/` on Windows.

---

## Compilation Types

### Incremental Build (Manual Steps Required)

For editing existing files. Takes ~30 seconds to 10 minutes.

**IMPORTANT:** Due to the Docker timestamp sync issue, you must follow the manual steps in the Quick Reference section above. The key steps are:

1. Verify Docker is healthy (`echo 'Docker OK'`)
2. Stop worldserver (`pkill -9 worldserver`)
3. Touch **only** the changed module's source files (`find ... | xargs touch`)
4. Run `make -j12 modules`
5. Run `make -j12 worldserver`
6. Run `make install` + `chmod +x worldserver`
7. Restart the container

**CRITICAL: Never touch files in modules you didn't change.** Touching `mod-playerbots` source files triggers a full rebuild of hundreds of files (~2 hours). Always scope the `find` command to the specific module.

### Full Rebuild

Required after adding new modules or changing CMakeLists.txt. Takes ~2 hours. Runs `cmake` to regenerate the build system, then `make` and `make install`.

See the Quick Reference section above for the full command.

### When to Use Each

| Change Type | Build Type | Time |
|-------------|------------|------|
| Edit `.cpp` file | Incremental | ~30s |
| Edit `.h` header | Incremental | Minutes (recompiles dependents) |
| Add new `.cpp` to existing module | Incremental | ~30s |
| Add NEW module | Full (`--full`) | ~2 hours |
| Change CMakeLists.txt | Full (`--full`) | ~2 hours |
| Edit Python/config files | None | Restart service |

---

## Clean Build (Start From Scratch)

Use when you need to completely rebuild everything from zero.

**WARNING:** This takes 2-3 hours. Only do this when necessary.

### Step 1: Backup Database First

```bash
docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/backup-database.sh
```

### Step 2: Delete Old Binaries (Windows Host)

The binaries live on Windows, not in Docker volumes. Delete them:

```powershell
# In PowerShell or delete via File Explorer
Remove-Item -Path "C:\azerothcore-wotlk\env\dist\bin\worldserver" -Force
Remove-Item -Path "C:\azerothcore-wotlk\env\dist\bin\authserver" -Force
```

**Note:** Keep `worldserver.exe` if you have a Windows build you want to preserve.

### Step 3: Remove Docker Build Volumes

```bash
# Stop containers
docker compose --profile dev down

# Remove build volumes (keeps database!)
docker volume rm azerothcore-wotlk_ac-build-dev
docker volume rm azerothcore-wotlk_ac-ccache-dev
```

**NEVER use `docker compose down -v`** - this deletes the database!

### Step 4: Start Container and Fix Permissions

```bash
# Start dev server
docker compose --profile dev up -d

# Wait for container to start
sleep 5

# Fix ccache permissions (required after volume recreation)
docker exec -u root azerothcore-wotlk-ac-dev-server-1 mkdir -p /azerothcore/var/ccache
docker exec -u root azerothcore-wotlk-ac-dev-server-1 chown -R acore:acore /azerothcore/var/ccache
docker exec -u root azerothcore-wotlk-ac-dev-server-1 chmod -R 777 /azerothcore/var/ccache
```

### Step 5: Run Full Build

```bash
docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/compile.sh --full
```

---

## Verifying Compilation

### Check If Build Is Running

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 ps aux"
```

Look for `make`, `cmake`, or `cc1plus` processes.

### Check Build Progress

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 tail -20 /tmp/compile.log"
```

### Verify New Binaries Were Created

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 ls -la /azerothcore/env/dist/bin/"
```

Check the timestamps on `worldserver` and `authserver` - they should show today's date.

### Check ccache Stats

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'CCACHE_DIR=/azerothcore/var/ccache ccache -s'"
```

After a clean build, you'll see many "cache miss" entries. Subsequent builds will show "cache hit".

---

## Avoiding Full Rebuilds

Full rebuilds take 2 hours. **Never do these unless necessary:**

| Action | Why It's Bad |
|--------|--------------|
| Delete `var/build/obj` contents | Forces full rebuild |
| Run `ccache -C` | Clears compiler cache |
| Delete the dev-server container | Loses build volume |
| Run `cmake` manually | Reconfigures everything |
| Delete build Docker volumes | Forces cmake + full make |

**cmake is NOT needed for:**
- Editing existing `.cpp` or `.h` files
- Adding new `.cpp` files to existing modules
- Changing config or SQL files

---

## Module Development

### File Locations

| Content | Path |
|---------|------|
| Module source | `modules/<mod-name>/src/` |
| Config template | `modules/<mod-name>/conf/*.conf.dist` |
| SQL migrations | `modules/<mod-name>/data/sql/` |
| Active configs | `env/dist/etc/modules/` |
| Build output | `/azerothcore/var/build/obj/` (Docker volume) |
| Installed binaries | `env/dist/bin/` (Windows) |

### Development Cycle

**For C++ changes:**
1. Edit source files in VS Code (files are on Windows, mounted into container)
2. Ask user for permission to compile
3. Follow the incremental build steps in Quick Reference above
4. Restart container after install
5. Test in-game

**For Python changes:**
1. Edit Python files
2. Restart bridge: `docker restart ac-llm-guide-bridge`
3. Test in-game

**For config changes:**
1. Edit config in `env/dist/etc/modules/`
2. Restart relevant service
3. Test in-game

---

## Troubleshooting

### Docker Commands Produce No Output (Windows/Git Bash)

**Problem:** Docker commands run in Git Bash on Windows produce no output, even with exit code 0.

**Affected:**
- `docker logs ...`
- `docker exec ... mysql -e "..."`
- `docker ps`

**NOT affected:**
- `docker exec ... bash /script.sh` (script runs inside container)

**Solution:** Use PowerShell wrapper:

```powershell
powershell.exe -Command "docker logs -f azerothcore-wotlk-ac-dev-server-1"
powershell.exe -Command "docker exec ac-database mysql -uroot -ppassword -e 'SHOW DATABASES'"
powershell.exe -Command "docker ps"
```

### ccache Permission Denied

**Problem:** After recreating Docker volumes, compilation fails with:
```
ccache: error: Failed to create directory /azerothcore/var/ccache/tmp: Permission denied
```

**Solution:** Fix permissions:

```bash
docker exec -u root azerothcore-wotlk-ac-dev-server-1 chown -R acore:acore /azerothcore/var/ccache
docker exec -u root azerothcore-wotlk-ac-dev-server-1 chmod -R 777 /azerothcore/var/ccache
```

### Build Doesn't Detect My Changes

Windows/Docker file timestamps sometimes don't sync. Touch the file:

```bash
docker exec azerothcore-wotlk-ac-dev-server-1 touch /azerothcore/modules/mod-llm-guide/src/LLMGuideScript.cpp
```

### Force Rebuild a Single Module

Delete only that module's object files:

```bash
docker exec azerothcore-wotlk-ac-dev-server-1 rm -f /azerothcore/var/build/obj/modules/CMakeFiles/modules.dir/mod-llm-guide/src/*.o
```

Then run incremental build.

### "No Makefile found" Error

You need to run a full build first (see Quick Reference above).

### "Failed to find map files"

Add the map data volume to docker-compose.yml under `ac-dev-server`:

```yaml
volumes:
  - ${DOCKER_VOL_DATA:-ac-client-data}:/azerothcore/env/dist/data/:ro
```

### "Could not connect to MySQL"

Use `ac-database` as hostname, not `localhost`. The container name is the DNS name inside Docker network.

### Docker VHDX Disk Bloat (Windows)

**Problem:** The Docker virtual disk (`docker_data.vhdx`) grows over time but never shrinks automatically. It can reach hundreds of GB even when actual Docker usage is much lower.

**Check actual usage:**
```powershell
docker system df
```

**Safe cleanup (does NOT touch ccache or volumes):**
```powershell
docker image prune -a -f
docker builder prune -f
```

**Compact the VHDX (requires Admin PowerShell):**
```powershell
# 1. Stop Docker Desktop first, then:
wsl --shutdown

# 2. Run in Admin PowerShell:
Optimize-VHD -Path "C:\Users\Calwen\AppData\Local\Docker\wsl\disk\docker_data.vhdx" -Mode Full

# 3. Restart Docker Desktop
```

**WARNING:** Never use `docker system prune --volumes` or `docker volume prune` — these delete named volumes including the ccache compilation cache (`ac-ccache-dev`).

### Permission Denied (Exit Code 126) After Install

**Problem:** `make install` can strip the execute permission on the worldserver binary. The container starts but worldserver fails with exit code 126.

**Solution:** Always `chmod +x` after install (already included in the Quick Reference steps):

```bash
chmod +x /azerothcore/env/dist/bin/worldserver
```

### Corrupted libmodules.a ("no more archived files")

**Problem:** Linker error: `error adding symbols: no more archived files`

**Solution:** Delete the corrupted library and rebuild:

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 rm -f /azerothcore/var/build/obj/modules/libmodules.a"
```

Then run the incremental build steps again.

### Linker Error: AddModulesScripts() Undefined

**Problem:** After certain changes, the linker can't find `AddModulesScripts()`.

**Solution:** Touch only the generated loader object, NOT all module sources:

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'touch /azerothcore/var/build/obj/modules/CMakeFiles/modules.dir/gen_scriptloader/static/ModulesLoader.cpp.o'"
```

Then rebuild modules and link worldserver.

### Compilation Seems Stuck

Check if processes are actually running:

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 ps aux"
```

If no `make`/`cmake`/`cc1plus` processes, the build may have failed. Check the log:

```powershell
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 cat /tmp/compile.log"
```

---

## Container Architecture

| Container | Purpose |
|-----------|---------|
| `azerothcore-wotlk-ac-dev-server-1` | Development worldserver (compiles from source) |
| `ac-worldserver` | Production server (pre-built binaries) |
| `ac-database` | MySQL database (shared by all) |
| `ac-llm-guide-bridge` | mod-llm-guide Python service |
| `ac-llm-chatter-bridge` | mod-llm-chatter Python service |

**Key insight:** Production containers use pre-built binaries. To test C++ changes, use the dev-server.

---

## Container Networking

**Inside Docker containers:**
- Database: `ac-database:3306`
- Use container names as hostnames

**From host machine:**
- Database: `localhost:3306`
- Worldserver: `localhost:8085`

---

## Scripts Reference

Scripts are located in `apps/docker/`:

| Script | Purpose | Run From |
|--------|---------|----------|
| `backup-database.sh` | Backup databases | Inside container |
| `start-dev-servers.sh` | Container entrypoint | Auto (Docker) |

**Note:** We no longer use `compile.sh` for builds. Incremental and full builds use manual `make` commands (see Quick Reference).

---

## Code Reference

### Player Data Access

```cpp
player->GetName()           // Character name
player->GetLevel()          // Level
player->getClass()          // Class ID
player->getRace()           // Race ID
player->GetAreaId()         // Zone ID
player->GetMoney()          // Copper
player->GetGroup()          // Group (nullptr if solo)
```

### Database Queries

```cpp
// Async (preferred) - uses fmt::format, NOT parameterized
CharacterDatabase.Execute(
    "INSERT INTO table VALUES ({}, '{}')", guid, value);

// IMPORTANT: Always EscapeString() user-derived strings
// (quest names, zone names, chat messages, etc.)
std::string safe = value;
CharacterDatabase.EscapeString(safe);
CharacterDatabase.Execute(
    "INSERT INTO table VALUES ({}, '{}')", guid, safe);

// Sync (use sparingly)
QueryResult result = CharacterDatabase.Query(
    "SELECT * FROM table WHERE id = {}", id);
if (result) {
    Field* fields = result->Fetch();
    uint32 val = fields[0].Get<uint32>();
}
```

### DBC Data

```cpp
#include "DBCStores.h"

if (AreaTableEntry const* area = sAreaTableStore.LookupEntry(zoneId))
    std::string name = area->area_name[0];
```
