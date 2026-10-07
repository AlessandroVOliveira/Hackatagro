// Sensor da armadilha coletiva (curral com porteira de queda).
// ESP32 + chave magnética (reed switch) na porteira. Quando a porteira cai,
// avisa o servidor da Ronda do Pampa, que chama o responsável da semana.
//
// Este exemplo usa Wi-Fi (sede ou roteador 4G perto da armadilha). No campo,
// sem Wi-Fi, troque o envio por um rádio LoRa até um gateway na sede ou por um
// módulo GSM mandando SMS; o servidor recebe o mesmo POST do gateway.

#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_NOME = "sede";
const char* WIFI_SENHA = "trocar";
const char* SERVIDOR = "http://192.168.0.10:8700/api/dispositivos/1/sensor";
const char* TOKEN = "";              // igual a RONDA_SENSOR_TOKEN no servidor
const int PINO_PORTEIRA = 27;        // reed switch entre o pino e o GND

bool fechadaAntes = false;

void avisar(const char* evento) {
  if (WiFi.status() != WL_CONNECTED) WiFi.reconnect();
  HTTPClient http;
  http.begin(SERVIDOR);
  http.addHeader("Content-Type", "application/json");
  if (strlen(TOKEN)) http.addHeader("x-sensor-token", TOKEN);
  int codigo = http.POST(String("{\"evento\":\"") + evento + "\"}");
  Serial.printf("%s -> %d\n", evento, codigo);
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_PORTEIRA, INPUT_PULLUP);
  WiFi.begin(WIFI_NOME, WIFI_SENHA);
}

void loop() {
  // ímã encostado = porteira aberta (armada); ímã longe = porteira caiu
  bool fechada = digitalRead(PINO_PORTEIRA) == HIGH;
  if (fechada != fechadaAntes) {
    delay(200);  // filtra o tranco da porteira
    if ((digitalRead(PINO_PORTEIRA) == HIGH) == fechada) {
      avisar(fechada ? "fechou" : "armada");
      fechadaAntes = fechada;
    }
  }
  delay(100);
}
