# Makefile du portage Tesseract (client WebAssembly), branche tesseract
#   make web   (après `source emsdk_env.sh`)
WEB_OUT ?= ../dist-tess/cube2
BUILD   ?= build
EMCXX ?= em++
EMCC  ?= emcc
INCLUDES = -Isrc/shared -Isrc/engine -Isrc/fpsgame -Isrc/enet/include
COMMONFLAGS = -fsigned-char -fno-exceptions -fno-rtti -w
WEB_OPT ?= -O2
WEB_DEBUG ?=
WEB_PORTS = -sUSE_ZLIB=1 -sUSE_SDL=2 -sUSE_SDL_IMAGE=2 -sSDL2_IMAGE_FORMATS='["png","jpg"]' -sUSE_SDL_MIXER=2 -sSDL2_MIXER_FORMATS='["ogg"]'
WEB_CXXFLAGS = $(WEB_OPT) -std=gnu++14 $(COMMONFLAGS) $(WEB_PORTS) $(INCLUDES) -DPORTFOLIO_WEB
ENET_SRCS = callbacks.c compress.c host.c list.c packet.c peer.c protocol.c unix.c
CLIENT_SRCS = \
	shared/crypto.cpp shared/geom.cpp shared/glemu.cpp shared/stream.cpp shared/tools.cpp shared/zip.cpp \
	engine/aa.cpp engine/bih.cpp engine/blend.cpp engine/client.cpp engine/command.cpp engine/console.cpp \
	engine/dynlight.cpp engine/grass.cpp engine/light.cpp engine/main.cpp engine/material.cpp engine/menus.cpp \
	engine/movie.cpp engine/normal.cpp engine/octa.cpp engine/octaedit.cpp engine/octarender.cpp \
	engine/physics.cpp engine/pvs.cpp engine/rendergl.cpp engine/renderlights.cpp engine/rendermodel.cpp \
	engine/renderparticles.cpp engine/rendersky.cpp engine/rendertext.cpp engine/renderva.cpp \
	engine/server.cpp engine/serverbrowser.cpp engine/shader.cpp engine/sound.cpp engine/stain.cpp \
	engine/texture.cpp engine/ui.cpp engine/water.cpp engine/world.cpp engine/worldio.cpp engine/webport.cpp \
	fpsgame/ai.cpp fpsgame/client.cpp fpsgame/entities.cpp fpsgame/fps.cpp fpsgame/nosp.cpp fpsgame/render.cpp \
	fpsgame/scoreboard.cpp fpsgame/server.cpp fpsgame/waypoint.cpp fpsgame/weapon.cpp fpsgame/portfolio.cpp fpsgame/tessgame.cpp
WEB_OBJS = $(addprefix $(BUILD)/web/,$(CLIENT_SRCS:.cpp=.o)) $(addprefix $(BUILD)/web/enet/,$(ENET_SRCS:.c=.o))
EXPORTS = "['_main','_malloc','_free','_pf_execute','_pf_resize','_pf_grab','_pf_getyaw','_pf_getpitch','_pf_mousemove','_pf_mousepos','_pf_guiopen','_pf_guihover']"
RUNTIME = "['ccall','cwrap','UTF8ToString','FS','ENV','callMain']"
WEB_LDFLAGS = $(WEB_OPT) $(WEB_PORTS) \
	-sMAX_WEBGL_VERSION=2 -sMIN_WEBGL_VERSION=2 -sFULL_ES3=1 \
	-sINITIAL_MEMORY=134217728 -sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=2097152 \
	-sEXIT_RUNTIME=0 -sFORCE_FILESYSTEM=1 -sDISABLE_EXCEPTION_CATCHING=1 \
	-sEXPORTED_FUNCTIONS=$(EXPORTS) -sEXPORTED_RUNTIME_METHODS=$(RUNTIME) \
	-sMODULARIZE=0 -sENVIRONMENT=web -sINVOKE_RUN=1 -sERROR_ON_UNDEFINED_SYMBOLS=1 -lidbfs.js
.PHONY: web clean
web: $(WEB_OUT)/cube2.js
$(WEB_OUT)/cube2.js: $(WEB_OBJS)
	@mkdir -p $(WEB_OUT)
	$(EMCXX) $(WEB_OBJS) -o $@ $(WEB_LDFLAGS) $(WEB_DEBUG)
$(BUILD)/web/%.o: src/%.cpp
	@mkdir -p $(dir $@)
	$(EMCXX) $(WEB_CXXFLAGS) -MMD -MP -c -o $@ $<
$(BUILD)/web/enet/%.o: src/enet/%.c
	@mkdir -p $(dir $@)
	$(EMCC) $(WEB_OPT) -Isrc/enet/include -DHAS_SOCKLEN_T=1 -w -c -o $@ $<
-include $(WEB_OBJS:.o=.d)
clean:
	rm -rf $(BUILD) $(WEB_OUT)
