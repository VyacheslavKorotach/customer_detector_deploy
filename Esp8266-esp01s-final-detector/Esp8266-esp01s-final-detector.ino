// Trigger PIN connected to GPIO2 (D4) of ESP8266 ESP-01S module
// ECHO PIN of ultrasonic sensor connected to GPIO0 (D3)

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Ultrasonic.h>

#define TRIGGER_PIN  2
#define ECHO_PIN     0

Ultrasonic ultrasonic(TRIGGER_PIN, ECHO_PIN);

const char *topic_pub_state = "customer_detector/exchanges/state/detector_0011";
const char *topic_pub_event = "customer_detector/exchanges/events/detector_0011";
const char *topic_sub1 = "customer_detector/exchanges/ctl/detector_0011";
const char *mqtt_device_id = "customer_detector_0011";

const char *ssid =  "otd";  // Имя вайфай точки доступа
const char *pass =  "220"; // Пароль от точки доступа

const char *mqtt_server = "mosquitto.ex-money.in.ua"; // Имя сервера MQTT
const int mqtt_port = 1883; // Порт для подключения к серверу MQTT
const char *mqtt_user = "otd"; // Логи от сервер
const char *mqtt_pass = "220"; // Пароль от сервера

int tm=300;
bool customer_detected = false;
bool obstacles = false;
float detect_distance = 50.0;
int times_to_change = 5;
int times_to_change_g = times_to_change;

float cmMsec, inMsec;
//long microsec = ultrasonic.timing();

String Customer_event = "No Customer";
int time1 = millis();
bool cust_stat = false;
int time3 = millis();

// Функция получения данных от сервера

void callback(const MQTT::Publish& pub)
{
  Serial.print(pub.topic());   // выводим в сериал порт название топика
  Serial.print(" => ");
  Serial.println(pub.payload_string()); // выводим в сериал порт значение полученных данных

  char payload[200];
  pub.payload_string().toCharArray(payload, 200);
  
  if(String(pub.topic()) == topic_sub1) // проверяем из нужного ли нам топика пришли данные 
  {
    DynamicJsonBuffer jsonBuffer(200);
    JsonObject& root = jsonBuffer.parseObject(payload);
    if (!root.success()) {
      Serial.println("JSON parsing failed!");
      return;
    } else {
        Serial.println("Here we run some command if it needed.");
    }
  }
}

WiFiClient wclient;      
PubSubClient client(wclient, mqtt_server, mqtt_port);

void setup() {
  Serial.begin(115200);
}

void loop() {
  // подключаемся к wi-fi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connecting to ");
    Serial.print(ssid);
    Serial.println("...");
    WiFi.begin(ssid, pass);

    if (WiFi.waitForConnectResult() != WL_CONNECTED)
      return;
    Serial.println("WiFi connected");
  }

  // подключаемся к MQTT серверу
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      Serial.println("Connecting to MQTT server");
      if (client.connect(MQTT::Connect(mqtt_device_id)
                         .set_auth(mqtt_user, mqtt_pass))) {
        Serial.println("Connected to MQTT server");
        client.set_callback(callback);
        client.subscribe(topic_sub1); // подписывааемся по топик с данными для насоса крипто-бармена
      } else {
        Serial.println("Could not connect to MQTT server");   
      }
    }

    if (client.connected()){
      client.loop();
      CustomerEventSend();
      ReadySend();
      delay(2000);
    }  
  }
} // конец основного цикла


// Функция отправки в соотв. топик MQTT брокера признака готовности устройства
void ReadySend(){
//  if (tm<=0)
//  {
    String ready_status = "Ready";
    String customer_status = "left";
    bool cust_stat_old = cust_stat;
    if (cmMsec <= detect_distance) {
      customer_status = "here";
      cust_stat = true;
    } else {
      cust_stat = false;
    }
    int time5 = millis();
    int duration = time5 - time3;
    if (cust_stat_old != cust_stat) {
      time3 = time5;
      duration = 0;
    }
    client.publish(topic_pub_state, "{\"status\": \"" + ready_status + "\", \"customer\": \"" + customer_status + "\", \"duration\": " + duration + ", \"obstacles\": " + cmMsec + "}");
    Serial.println(ready_status);
//    tm = 300;  // пауза меду отправками признака готовности около 3 секунд
//  }
//  tm--; 
    delay(10);  
}

void CustomerEventSend(){
//  float cmMsec, inMsec;
  long microsec = ultrasonic.timing();

  cmMsec = ultrasonic.convert(microsec, Ultrasonic::CM);
  inMsec = ultrasonic.convert(microsec, Ultrasonic::IN);
  Serial.print("MS: ");
  Serial.print(microsec);
  Serial.print(", CM: ");
  Serial.print(cmMsec);
  Serial.print(", IN: ");
  Serial.println(inMsec);
  if (cmMsec > detect_distance) {
    obstacles = false;
  }
  else {
    obstacles = true;
  }
  bool customer_detected_old = customer_detected;
  Serial.println("Obstacles = " + String(obstacles));
  if (customer_detected != obstacles) {
    times_to_change_g -= 1;
    if (times_to_change_g <= 0) {
      customer_detected = obstacles;
      times_to_change_g = times_to_change;
    }
  } else {
    times_to_change_g = times_to_change;
  }
  if (customer_detected_old != customer_detected) {
    int time2 = millis();
    int duration = time2 - time1;
    time1 = time2;
    if (customer_detected) {
      Customer_event = "Customer arraived";
      client.publish(topic_pub_event, "{\"event\": \"" + Customer_event + "\", \"duration\": " + duration + "}");
    } else {
      Customer_event = "Customer left";
      client.publish(topic_pub_event, "{\"event\": \"" + Customer_event + "\", \"duration\": " + duration + "}");
    }
  }
  delay(100); 
}
