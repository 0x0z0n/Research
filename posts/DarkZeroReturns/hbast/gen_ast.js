const Handlebars = require('handlebars');
console.log(JSON.stringify(Handlebars.parse('{{lookup this 1}}'), null, 2));
