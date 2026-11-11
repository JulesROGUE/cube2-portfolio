# Makefile du moteur Cube 2 « portfolio »
#
#   make web      -> client WebAssembly (emcc, à lancer après `source emsdk_env.sh`)
#   make server   -> serveur dédié natif Linux (g++)
#
# Les objets du client et du serveur sont séparés (build/web, build/server).

WEB_OUT ?= ../dist/cube2
BUILD   ?= build

EMCXX ?= em++
EMCC  ?= emcc
CXX_NATIVE ?= g++
CC_NATIVE  ?= gcc

INCLUDES = -Ishared -Iengine -Ifpsgame -Ienet/include

COMMONFLAGS = -fsigned-char -fno-exceptions -fno-rtti -w
WEB_OPT ?= -Oz
WEB_PORTS = -sUSE_ZLIB=1 -sUSE_SDL=2 -sUSE_SDL_IMAGE=2 -sSDL2_IMAGE_FORMATS='["png","jpg"]' -sUSE_SDL_MIXER=2 -sSDL2_MIXER_FORMATS='["ogg"]'
WEB_CXXFLAGS = $(WEB_OPT) -std=gnu++03 $(COMMONFLAGS) $(WEB_PORTS) $(INCLUDES) -DPORTFOLIO_WEB
SRV_CXXFLAGS = -O2 -std=gnu++03 $(COMMONFLAGS) $(INCLUDES) -DSTANDALONE -DPORTFOLIO_SERVER

ENET_SRCS = callbacks.c compress.c host.c list.c packet.c peer.c protocol.c unix.c

CLIENT_SRCS = \
	shared/crypto.cpp shared/geom.cpp shared/glemu.cpp shared/stream.cpp shared/tools.cpp shared/zip.cpp \
	engine/3dgui.cpp engine/bih.cpp engine/blend.cpp engine/blob.cpp engine/client.cpp engine/command.cpp \
	engine/console.cpp engine/cubeloader.cpp engine/decal.cpp engine/dynlight.cpp engine/glare.cpp \
	engine/grass.cpp engine/lightmap.cpp engine/main.cpp engine/material.cpp engine/menus.cpp \
	engine/normal.cpp engine/octa.cpp engine/octaedit.cpp engine/octarender.cpp \
	engine/physics.cpp engine/pvs.cpp engine/rendergl.cpp engine/rendermodel.cpp \
	engine/renderparticles.cpp engine/rendersky.cpp engine/rendertext.cpp engine/renderva.cpp \
	engine/server.cpp engine/serverbrowser.cpp engine/shader.cpp engine/shadowmap.cpp engine/sound.cpp engine/webstubs.cpp engine/pfweb.cpp \
	engine/texture.cpp engine/water.cpp engine/world.cpp engine/worldio.cpp \
	fpsgame/ai.cpp fpsgame/client.cpp fpsgame/entities.cpp fpsgame/fps.cpp fpsgame/monster.cpp \
	fpsgame/movable.cpp fpsgame/render.cpp fpsgame/scoreboard.cpp fpsgame/server.cpp \
	fpsgame/waypoint.cpp fpsgame/weapon.cpp fpsgame/portfolio.cpp

SERVER_SRCS = \
	shared/crypto.cpp shared/stream.cpp shared/tools.cpp \
	engine/command.cpp engine/server.cpp engine/worldio.cpp \
	fpsgame/entities.cpp fpsgame/server.cpp

WEB_OBJS = $(addprefix $(BUILD)/web/,$(CLIENT_SRCS:.cpp=.o)) $(addprefix $(BUILD)/web/enet/,$(ENET_SRCS:.c=.o))
SRV_OBJS = $(addprefix $(BUILD)/server/,$(SERVER_SRCS:.cpp=.o)) $(addprefix $(BUILD)/server/enet/,$(ENET_SRCS:.c=.o))

EXPORTS = "['_main','_malloc','_free','_pf_execute','_pf_resize','_pf_grab','_pf_getyaw','_pf_getpitch','_pf_mousemove']"
RUNTIME = "['ccall','cwrap','UTF8ToString','FS','ENV','callMain']"

WEB_LDFLAGS = $(WEB_OPT) $(WEB_PORTS) \
	-sMAX_WEBGL_VERSION=2 -sMIN_WEBGL_VERSION=2 -sFULL_ES3=1 \
	-sINITIAL_MEMORY=67108864 -sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=1048576 \
	-sEXIT_RUNTIME=0 -sFORCE_FILESYSTEM=1 -sDISABLE_EXCEPTION_CATCHING=1 \
	-sEXPORTED_FUNCTIONS=$(EXPORTS) -sEXPORTED_RUNTIME_METHODS=$(RUNTIME) \
	-sMODULARIZE=0 -sENVIRONMENT=web -sINVOKE_RUN=1 -sERROR_ON_UNDEFINED_SYMBOLS=1 \
	-lidbfs.js

.PHONY: all web server clean
all: web server

web: $(WEB_OUT)/cube2.js
server: $(BUILD)/cube2_server

$(WEB_OUT)/cube2.js: $(WEB_OBJS)
	@mkdir -p $(WEB_OUT)
	$(EMCXX) $(WEB_OBJS) -o $@ $(WEB_LDFLAGS)

$(BUILD)/cube2_server: $(SRV_OBJS)
	$(CXX_NATIVE) -o $@ $(SRV_OBJS) -lz

$(BUILD)/web/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(EMCXX) $(WEB_CXXFLAGS) -c -o $@ $<

$(BUILD)/web/enet/%.o: enet/%.c
	@mkdir -p $(dir $@)
	$(EMCC) $(WEB_OPT) -Ienet/include -DHAS_SOCKLEN_T=1 -w -c -o $@ $<

$(BUILD)/server/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX_NATIVE) $(SRV_CXXFLAGS) -c -o $@ $<

$(BUILD)/server/enet/%.o: enet/%.c
	@mkdir -p $(dir $@)
	$(CC_NATIVE) -O2 -Ienet/include -DHAS_SOCKLEN_T=1 -DHAS_POLL=1 -DHAS_FCNTL=1 -DHAS_MSGHDR_FLAGS=1 -w -c -o $@ $<

clean:
	rm -rf $(BUILD) $(WEB_OUT)/cube2.js $(WEB_OUT)/cube2.wasm
