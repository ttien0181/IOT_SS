const mysql = require('mysql')
const connection = mysql.createConnection({
	host:'localhost',
	user:'mobius',
	password:'mobius',
	database:'mobiusdb'
});

connection.connect(function(err) {
	if (err) throw err;
	console.log("Connected");
	connection.end();
});
