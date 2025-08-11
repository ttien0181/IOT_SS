/**
 * Copyright (c) 2018, KETI
 * All rights reserved.
 */

var mariadb = require('mariadb');

var mariadb_pool = null;

exports.connect = function (host, port, user, password, callback) {
    mariadb_pool = mariadb.createPool({
        host: host,
        port: port || 3306,
        user: user,
        password: password,
        database: 'mobiusdb',
        connectionLimit: 100,
        acquireTimeout: 50000
    });

    callback('1');
};

exports.getConnection = function(callback) {
    if (mariadb_pool == null) {
        console.error("MariaDB is not connected");
        callback(true, "MariaDB is not connected");
        return '0';
    }

    mariadb_pool.getConnection()
        .then(conn => {
            callback('200', conn);
        })
        .catch(err => {
            console.error("Failed to get MariaDB connection:", err);
            callback('500-5');
        });
};

exports.getResult = function(query, connection, callback) {
    if (mariadb_pool == null) {
        console.error("MariaDB is not connected");
        return '0';
    }

    connection.query({ sql: query, timeout: 60000 })
        .then(rows => {
            callback(null, rows);
        })
        .catch(err => {
            callback(true, err);
        });
};