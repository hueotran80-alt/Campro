// mqtt-worker/bridge.js
// ============================================================
// MQTT <-> Supabase bridge
// ESP8266 <-> MQTT <-> Bridge <-> Supabase
// ============================================================

import "dotenv/config";
import mqtt from "mqtt";
import { createClient } from "@supabase/supabase-js";
import { createServer } from "node:http";

// ============================================================
// CẤU HÌNH
// ============================================================

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_ROLE_KEY =
  process.env.SUPABASE_SERVICE_ROLE_KEY;

const MQTT_URL =
  process.env.MQTT_URL ||
  "mqtt://broker.hivemq.com:1883";

const DEVICE_CODE = "ESP-MAIN-DOOR";

// Firmware hiện tại heartbeat mỗi 5 giây.
// Cho phép tối đa thêm ~1 chu kỳ ngắn để đánh dấu offline.
const OFFLINE_TIMEOUT_MS = 6500;

// ============================================================
// KIỂM TRA ENV
// ============================================================

if (!SUPABASE_URL || !SERVICE_ROLE_KEY) {
  console.error(
    "❌ Thiếu SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY trong .env"
  );

  process.exit(1);
}

// ============================================================
// SUPABASE
// ============================================================

const supabase = createClient(
  SUPABASE_URL,
  SERVICE_ROLE_KEY
);

// ============================================================
// MQTT TOPIC
// ============================================================

const TOPIC_COMMAND =
  "smartbuilding/door/command";

const TOPIC_STATE =
  "smartbuilding/door/state";

const TOPIC_EVENT =
  "smartbuilding/door/event";

// ============================================================
// BIẾN TRẠNG THÁI
// ============================================================

let deviceId = null;
let lastSeen = 0;
let markedOffline = false;

// ============================================================
// TÌM ESP-MAIN-DOOR
// Database dùng device_code, KHÔNG phải device_uid
// ============================================================

async function ensureDevice() {
  if (deviceId) {
    return deviceId;
  }

  const { data, error } = await supabase
    .from("devices")
    .select("id")
    .eq("device_code", DEVICE_CODE)
    .single();

  if (error || !data) {
    console.error(
      "❌ Không tìm thấy ESP-MAIN-DOOR trong devices:",
      error
    );

    return null;
  }

  deviceId = data.id;

  console.log(
    "✅ Tìm thấy ESP-MAIN-DOOR:",
    deviceId
  );

  return deviceId;
}

// ============================================================
// CẬP NHẬT ONLINE / OFFLINE
// ============================================================

async function markOnline(online) {
  const id = await ensureDevice();

  if (!id) {
    return;
  }

  const devicePayload = {
    online,
    ...(online
      ? { last_seen: new Date().toISOString() }
      : {}),
  };

  const { error: deviceError } =
    await supabase
      .from("devices")
      .update(devicePayload)
      .eq("id", id);

  if (deviceError) {
    console.error(
      "❌ Không cập nhật được devices:",
      deviceError
    );
  }

  const { error: stateError } =
    await supabase
      .from("door_states")
      .update({
        device_online: online,
        updated_at: new Date().toISOString(),
      })
      .eq("device_id", id);

  if (stateError) {
    console.error(
      "❌ Không cập nhật được door_states:",
      stateError
    );
  }

  markedOffline = !online;

  console.log(
    `[bridge] ESP-MAIN-DOOR = ${online ? "ONLINE" : "OFFLINE"}`
  );
}

// ============================================================
// CẬP NHẬT TRẠNG THÁI CỬA
// ESP gửi:
//   UNLOCKED
//   LOCKED
//   WRONG_PIN
// ============================================================

async function applyState(payload) {
  const value = payload
    .toString()
    .trim();

  lastSeen = Date.now();

  const id = await ensureDevice();

  if (!id) {
    return;
  }

  console.log(
    "[bridge] State từ ESP:",
    value
  );

  if (value === "OFFLINE") {
    await markOnline(false);
    console.log("⚠ [bridge] ESP-MAIN-DOOR OFFLINE từ MQTT/LWT.");
    return;
  }

  await supabase
    .from("devices")
    .update({
      online: true,
      last_seen: new Date().toISOString(),
    })
    .eq("id", id);

  if (value === "UNLOCKED") {
    const { error } =
      await supabase
        .from("door_states")
        .update({
          lock_status: "UNLOCKED",
          door_status: "OPEN",
          device_online: true,
          updated_at: new Date().toISOString(),
        })
        .eq("device_id", id);

    if (error) {
      console.error(
        "❌ Lỗi cập nhật UNLOCKED:",
        error
      );
    }
  }

  else if (value === "LOCKED") {
    const { error } =
      await supabase
        .from("door_states")
        .update({
          lock_status: "LOCKED",
          door_status: "CLOSED",
          device_online: true,
          updated_at: new Date().toISOString(),
        })
        .eq("device_id", id);

    if (error) {
      console.error(
        "❌ Lỗi cập nhật LOCKED:",
        error
      );
    }
  }

  else if (value === "WRONG_PIN") {
    const { error } =
      await supabase
        .from("door_states")
        .update({
          device_online: true,
          updated_at: new Date().toISOString(),
        })
        .eq("device_id", id);

    if (error) {
      console.error(
        "❌ Lỗi cập nhật WRONG_PIN:",
        error
      );
    }
  }

  if (markedOffline) {
    await markOnline(true);
  }
}

// ============================================================
// GỬI LỆNH WEB QUA MQTT
// ============================================================

async function processPendingCommand() {
  if (!client.connected) {
    return;
  }

  const command = await getPendingCommand();

  if (!command) {
    return;
  }

  if (command.command !== "OPEN") {
    console.warn(
      "⚠ Lệnh PENDING không phải OPEN:",
      command.command
    );
    return;
  }

  const { data, error } = await supabase
    .from("door_commands")
    .update({
      status: "SENT",
    })
    .eq("id", command.id)
    .eq("status", "PENDING")
    .select("id")
    .maybeSingle();

  if (error) {
    console.error(
      "❌ Không chuyển door_commands sang SENT:",
      error
    );
    return;
  }

  if (!data) {
    return;
  }

  client.publish(
    TOPIC_COMMAND,
    "OPEN",
    { qos: 1 },
    async (publishError) => {
      if (publishError) {
        console.error(
          "❌ Không gửi được MQTT command:",
          publishError
        );

        await supabase
          .from("door_commands")
          .update({
            status: "FAILED",
          })
          .eq("id", command.id)
          .eq("status", "SENT");

        return;
      }

      console.log(
        "✅ Đã gửi MQTT command OPEN:",
        command.id
      );
    }
  );
}

// ============================================================
// LẤY LỆNH WEB ĐANG CHỜ
// ============================================================

async function getPendingCommand() {
  const id = await ensureDevice();

  if (!id) {
    return null;
  }

  const cutoff = new Date(
    Date.now() - 15000
  ).toISOString();

  const { data: staleCommands } = await supabase
    .from("door_commands")
    .update({
      status: "BLOCKED",
      block_reason: "Lệnh mở cửa đã quá 15 giây và hết hạn.",
      executed_at: new Date().toISOString(),
    })
    .eq("device_id", id)
    .eq("status", "PENDING")
    .lt("created_at", cutoff)
    .select("id");

  if (staleCommands?.length) {
    console.warn(
      "⚠ Đã chặn lệnh door_commands hết hạn:",
      staleCommands.map((row) => row.id)
    );
  }

  const { data, error } = await supabase
    .from("door_commands")
    .select("id, command, source, status, created_at")
    .eq("device_id", id)
    .eq("status", "PENDING")
    .gte("created_at", cutoff)
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle();

  if (error) {
    console.error(
      "❌ Không đọc được door_commands:",
      error
    );
    return null;
  }

  return data ?? null;
}

// ============================================================
// XỬ LÝ EVENT
// ============================================================

async function applyEvent(payload) {
  lastSeen = Date.now();

  let event;

  try {
    event = JSON.parse(
      payload.toString()
    );
  } catch {
    console.warn(
      "⚠ Event MQTT không phải JSON:",
      payload.toString()
    );

    return;
  }

  console.log(
    "[bridge] Event:",
    event
  );

  const id = await ensureDevice();

  if (!id) {
    return;
  }

  if (event.source === "Keypad Vat Ly") {
    const { error } = await supabase
      .from("access_logs")
      .insert({
        device_id: id,
        method: "KEYPAD",
        result:
          event.result === "SUCCESS"
            ? "SUCCESS"
            : "FAILED",
        person_name: "Bàn phím vật lý",
        room_number: null,
      });

    if (error) {
      console.error(
        "❌ Không ghi được access_logs:",
        error
      );
    } else {
      console.log(
        "✅ Đã ghi access_logs: KEYPAD"
      );
    }

    return;
  }

  if (event.source === "MQTT Web") {
    const { data: command, error: commandError } =
      await supabase
        .from("door_commands")
        .select(
          "id,user_id,occupant_id,source,created_at"
        )
        .eq("device_id", id)
        .eq("status", "SENT")
        .is("executed_at", null)
        .in("source", [
          "WEB",
          "WEB_PIN",
          "PHONE_BIOMETRIC",
          "FACE",
        ])
        .order("created_at", {
          ascending: false,
        })
        .limit(1)
        .maybeSingle();

    if (commandError) {
      console.error(
        "❌ Không tìm được door_command:",
        commandError
      );
      return;
    }

    if (!command) {
      console.warn(
        "⚠ Không tìm thấy door_command WEB đang chờ xử lý."
      );
      return;
    }

    const result =
      event.result === "SUCCESS"
        ? "SUCCESS"
        : "FAILED";

    let personName = null;
    let roomId = null;
    let roomNumber = null;
    let userId = command.user_id ?? null;

    if (command.occupant_id) {
      const { data: occupant, error: occupantError } =
        await supabase
          .from("room_occupants")
          .select("id,full_name,room_id")
          .eq("id", command.occupant_id)
          .maybeSingle();

      if (occupantError) {
        console.error(
          "❌ Không lấy được room_occupant:",
          occupantError
        );
        return;
      }

      personName = occupant?.full_name ?? null;
      roomId = occupant?.room_id ?? null;
    } else if (command.user_id) {
      const { data: profile, error: profileError } =
        await supabase
          .from("profiles")
          .select(
            "id,full_name,role,room_id"
          )
          .eq("id", command.user_id)
          .maybeSingle();

      if (profileError) {
        console.error(
          "❌ Không lấy được profile:",
          profileError
        );
        return;
      }

      personName = profile?.full_name ?? null;
      roomId = profile?.room_id ?? null;
    }

    if (roomId) {
      const { data: room, error: roomError } =
        await supabase
          .from("rooms")
          .select("room_number")
          .eq("id", roomId)
          .maybeSingle();

      if (roomError) {
        console.warn(
          "⚠ Không lấy được room_number:",
          roomError
        );
      } else {
        roomNumber = room?.room_number ?? null;
      }
    }

    const { error: logError } =
      await supabase
        .from("access_logs")
        .insert({
          user_id: userId,
          room_id: roomId,
          occupant_id: command.occupant_id ?? null,
          device_id: id,
          person_name: personName,
          room_number: roomNumber,
          method:
            command.source === "FACE"
              ? "FACE"
              : command.source,
          result,
        });

    if (logError) {
      console.error(
        "❌ Không ghi được access_logs:",
        logError
      );
      return;
    }

    const { error: updateError } =
      await supabase
        .from("door_commands")
        .update({
          status: result,
          executed_at: new Date().toISOString(),
          block_reason:
            result === "FAILED"
              ? "ESP báo thực thi thất bại."
              : null,
        })
        .eq("id", command.id)
        .eq("status", "SENT")
        .is("executed_at", null);

    if (updateError) {
      console.error(
        "❌ Không cập nhật trạng thái door_command:",
        updateError
      );
      return;
    }

    console.log(
      "✅ Đã xác nhận door_command:",
      command.id,
      command.source,
      personName ??
        command.occupant_id ??
        command.user_id ??
        "unknown",
      result
    );

    return;
  }

  console.log(
    "ℹ Bỏ qua MQTT event:",
    event.source
  );
}

// ============================================================
// MQTT
// ============================================================

const client = mqtt.connect(
  MQTT_URL,
  {
    reconnectPeriod: 3000,
    connectTimeout: 10000,
  }
);

// ============================================================
// RENDER HEALTH ENDPOINT
// ============================================================

const PORT = Number(
  process.env.PORT || 10000
);

const healthServer = createServer(
  (req, res) => {
    if (
      req.url === "/health" ||
      req.url === "/"
    ) {
      res.writeHead(
        200,
        {
          "content-type":
            "application/json",
        }
      );

      res.end(
        JSON.stringify({
          ok: true,
          mqtt_connected:
            client?.connected ??
            false,
          device: DEVICE_CODE,
        })
      );

      return;
    }

    res.writeHead(404);
    res.end("Not found");
  }
);

healthServer.listen(
  PORT,
  "0.0.0.0",
  () => {
    console.log(
      `[bridge] Health server listening on :${PORT}`
    );
  }
);

function shutdown(signal) {
  console.log(
    `[bridge] ${signal}: shutting down...`
  );

  healthServer.close();

  client.end(
    false,
    {},
    () => process.exit(0)
  );

  setTimeout(
    () => process.exit(1),
    5000
  ).unref();
}

process.on(
  "SIGTERM",
  () => shutdown("SIGTERM")
);

process.on(
  "SIGINT",
  () => shutdown("SIGINT")
);

// ============================================================
// MQTT CONNECT
// ============================================================

client.on(
  "connect",
  async () => {
    console.log(
      "================================================"
    );

    console.log(
      "✅ [bridge] Đã kết nối MQTT"
    );

    console.log(
      "Broker:",
      MQTT_URL
    );

    console.log(
      "Device:",
      DEVICE_CODE
    );

    console.log(
      "================================================"
    );

    client.subscribe(
      [
        TOPIC_STATE,
        TOPIC_EVENT,
      ],
      (error) => {
        if (error) {
          console.error(
            "❌ Subscribe MQTT lỗi:",
            error
          );

          return;
        }

        console.log(
          "✅ Đã subscribe:"
        );

        console.log(
          "   ",
          TOPIC_STATE
        );

        console.log(
          "   ",
          TOPIC_EVENT
        );
      }
    );
  }
);

// ============================================================
// MQTT MESSAGE
// ============================================================

client.on(
  "message",
  (topic, payload) => {
    console.log(
      `[MQTT] ${topic} -> ${payload.toString()}`
    );

    if (
      topic === TOPIC_STATE
    ) {
      applyState(
        payload
      ).catch(console.error);
    }

    if (
      topic === TOPIC_EVENT
    ) {
      applyEvent(
        payload
      ).catch(console.error);
    }
  }
);

// ============================================================
// KIỂM TRA LỆNH WEB ĐANG CHỜ
// ============================================================

setInterval(
  () => {
    processPendingCommand().catch(
      (error) => {
        console.error(
          "❌ Lỗi xử lý door command:",
          error
        );
      }
    );
  },
  1000
);

// ============================================================
// MQTT RECONNECT
// ============================================================

client.on(
  "reconnect",
  () => {
    console.log(
      "🔄 [bridge] Đang kết nối lại MQTT..."
    );
  }
);

// ============================================================
// MQTT ERROR
// ============================================================

client.on(
  "error",
  (error) => {
    console.error(
      "❌ [bridge] MQTT error:",
      error.message
    );
  }
);

// ============================================================
// MQTT OFFLINE
// ============================================================

client.on(
  "offline",
  () => {
    console.warn(
      "⚠ [bridge] MQTT offline"
    );
  }
);

// ============================================================
// KIỂM TRA ESP CÒN HOẠT ĐỘNG KHÔNG
// ============================================================

setInterval(
  () => {
    if (
      !markedOffline &&
      Date.now() - lastSeen >=
        OFFLINE_TIMEOUT_MS
    ) {
      console.warn(
        "⚠ Không nhận được dữ liệu từ ESP-MAIN-DOOR."
      );

      markOnline(
        false
      ).catch(console.error);
    }
  },
  1000
);

// ============================================================
// KHỞI ĐỘNG
// ============================================================

ensureDevice()
  .then(
    (id) => {
      if (id) {
        console.log(
          "✅ Bridge sẵn sàng cho:",
          DEVICE_CODE
        );
      }
    }
  )
  .catch(console.error);
