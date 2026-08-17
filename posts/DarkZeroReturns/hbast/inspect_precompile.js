const Handlebars = require('handlebars');
const compiled = Handlebars.precompile('{{lookup this 1}}');
console.log(compiled);
