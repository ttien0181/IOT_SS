/**
 * Created by Il Yeup, Ahn in KETI on 2017-02-25.
 */

/**
 * Copyright (c) 2018, OCEAN
 * All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// for TAS

global.socket_arr = {};

let tas_buffer = {};
exports.buffer = tas_buffer;


// for tas

let mqtt = require('mqtt');
let moment = require('moment');

/* USER CODE */
// let getDataTopic = {
//     bpm: 'hospital/floor1/room101/bpm',
//     spo2: 'hospital/floor1/room101/spo2',
//     temp: 'hospital/floor1/room101/temp',
// };

// [MODIFIED] Chỉ cần define root topics, không hardcode phòng/sensor
let rootTopics = [
    '#',      // subscribe tất cả các topic 
    // 'hospital2/#'      // subscribe tất cả các topic dưới hospital2
];

let setDataTopic = {
    led: '/led/set',
};
/* */


// [MODIFIED] Hàm tạo container động (bỏ bước kiểm tra)
function create_cnt_if_not_exist(pathParts, callback) {
    // pathParts = ["Mobius","HealthCareIoT","hospital","floor1","room101","temp"]
    let currentParent = '/' + pathParts[0] + '/' + pathParts[1]; // /Mobius/HealthCareIoT

    function createNext(index) {
        if (index >= pathParts.length) {
            return callback && callback();
        }

        let cntName = pathParts[index];
        let fullPath = currentParent + '/' + cntName;

        onem2m_client.create_cnt(currentParent, cntName, 'json', (status, res_body) => {
            console.log(`Create CNT ${fullPath} -> status ${status}`);
            currentParent = fullPath;
            createNext(index + 1);
        });
    }

    createNext(2); // bắt đầu tạo từ "hospital"
}





// Tạo kết nối MQTT đến broker và subscribe các topic root
let createConnection = () => {
    if (conf.tas.client.connected) {
        console.log('Already connected --> destroyConnection')
        destroyConnection();
    }

    if (!conf.tas.client.connected) {
        conf.tas.client.loading = true;
        const {host, port, endpoint, ...options} = conf.tas.connection;
        const connectUrl = `mqtt://${host}:${port}${endpoint}`
        try {
            conf.tas.client = mqtt.connect(connectUrl, options);

            conf.tas.client.on('connect', () => {
                console.log(host, 'Connection succeeded!');

                conf.tas.client.connected = true;
                conf.tas.client.loading = false;

                // for (let topicName in getDataTopic) {
                //     if (getDataTopic.hasOwnProperty(topicName)) {
                //         doSubscribe(getDataTopic[topicName]);
                //     }
                // }

                // [MODIFIED] Subscribe tất cả root topic
                rootTopics.forEach(topic => doSubscribe(topic));
            });

            conf.tas.client.on('error', (error) => {
                console.log('Connection failed', error);

                destroyConnection();
            });

            conf.tas.client.on('close', () => {
                console.log('Connection closed');

                destroyConnection();
            });

            // [MODIFIED] Parse topic động
            conf.tas.client.on('message', (topic, message) => {
                let content = null;
                let parent = null;

                try {
                    let data = JSON.parse(message.toString());
                    let parts = topic.split('/');
                    let building = parts[0]; // A1
                    let floor = parts[1]; // 1
                    let room = parts[2]; // 101
                    let sensor = parts[3]; // spo2

                    parent = `/Mobius/${conf.ae.name}/${building}/${floor}/${room}/${sensor}`;

                    // Chuẩn hóa payload CIN theo oneM2M
                    content = {
                        t: data.timestamp || new Date().toISOString(),
                        v: data.value,
                        u: data.unit || "",
                        sid: data.sensor_id || ""
                    };

                } catch (e) {
                    console.error("Invalid JSON from MQTT:", e);
                }

                // Tạo CIN nếu content hợp lệ
                if (content && parent) {
                    let pathParts = parent.split('/').filter(p => p);
                    create_cnt_if_not_exist(pathParts, () => {
                        onem2m_client.create_cin(
                            parent, 
                            4, // ty = 4 cho cin
                            JSON.stringify(content), 
                            null, // socket
                            (status) => {
                                console.log(`Created CIN for ${parent} → status: ${status}`);
                            }
                        );
                    });
                }
            });
        }
        catch (error) {
            console.log('mqtt.connect error', error);
            conf.tas.client.connected = false;
        }
    }
};


// Đăng ký (subscribe) một topic MQTT cụ thể
let doSubscribe = (topic) => {
    if (conf.tas.client.connected) {
        const qos = 0;
        conf.tas.client.subscribe(topic, {qos}, (error) => {
            if (error) {
                console.log('Subscribe to topics error', error)
                return;
            }

            console.log('Subscribe to topics (', topic, ')');
        });
    }
};


// Hủy đăng ký (unsubscribe) một topic MQTT cụ thể
let doUnSubscribe = (topic) => {
    if (conf.tas.client.connected) {
        conf.tas.client.unsubscribe(topic, error => {
            if (error) {
                console.log('Unsubscribe error', error)
            }

            console.log('Unsubscribe to topics (', topic, ')');
        });
    }
};


// Gửi (publish) một payload MQTT lên một topic
let doPublish = (topic, payload) => {
    if (conf.tas.client.connected) {
        conf.tas.client.publish(topic, payload, 0, error => {
            if (error) {
                console.log('Publish error', error)
            }
        });
    }
};

// Đóng kết nối MQTT hiện tại với broker
let destroyConnection = () => {
    if (conf.tas.client.connected) {
        try {
            if (Object.hasOwnProperty.call(conf.tas.client, '__ob__')) {
                conf.tas.client.end();
            }
            conf.tas.client = {
                connected: false,
                loading: false
            }
            console.log('Successfully disconnected!');
        }
        catch (error) {
            console.log('Disconnect failed', error.toString())
        }
    }
};

// Khởi tạo TAS: thiết lập kết nối và chạy chế độ giả lập (nếu bật)
exports.ready_for_tas = function ready_for_tas() {
    createConnection();

    /* ***** USER CODE ***** */
    if (conf.sim === 'enable') {
        let t_count = 0;
        setInterval(() => {
            let val = (Math.random() * 50).toFixed(1);
            doPublish('/thyme/co2', val);
        }, 5000, t_count);
    }
    /* */
};

// Gửi dữ liệu hoặc lệnh điều khiển từ nCube xuống TAS qua MQTT
exports.send_to_tas = function send_to_tas(topicName, message) {
    if (setDataTopic.hasOwnProperty(topicName)) {
        conf.tas.client.publish(setDataTopic[topicName], message.toString())
    }
};
