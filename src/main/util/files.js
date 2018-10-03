const fs = require("fs");

exports.writeFile = async (filename, contents) => {
    return new Promise((res, rej) => {
        fs.writeFile(filename, contents, err => {
            if (err) {
                rej(err);
            } else {
                res();
            }
        });
    });
}

exports.readFile = async filename => {
    return new Promise((res, rej) => {
        fs.readFile(filename, (err, data) => {
            if (err) {
                rej(err);
            } else {
                res(data);
            }
        });
    });
}