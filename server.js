var app = require('express')()
  , bodyParser = require('body-parser')
  , MongoClient = require('mongodb').MongoClient;

MongoClient.connect('mongodb://localhost:27017/raspi-stats', function (err, db) {
  if (err) {
    console.log(err);
    return;
  }
  
  app.use(bodyParser.json());
  app.post('/', function (req, res) {
    var data = req.body;

    if (!data || !data.nick || data.nick.length === 0) {
      console.log('Invalid data: %s', JSON.stringify(data));
      res.status(400).end();
    }
    else {
      db.collection('stats').insert(data, function (err, result) {
        if (err) {
          console.log(err);
        }

        res.status(err ? 500 : 201).end();
      });
    }
  });

  var server = app.listen(3000, function () {
    var port = server.address().port;

    console.log('Server listening at http://localhost:%s', port);
  });
});