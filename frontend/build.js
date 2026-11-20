// Vercel build-time configuration for a completely vanilla frontend.
// API_BASE_URL is a public endpoint, NOT an API secret.
const fs = require('fs');
const path = require('path');
const src = path.join(__dirname,'public');
const dest = path.join(__dirname,'dist');
fs.rmSync(dest,{recursive:true,force:true});
fs.cpSync(src,dest,{recursive:true});
const base = process.env.API_BASE_URL || '';
if (!base.startsWith('https://') && !base.startsWith('http://')) {
  console.warn('WARNING: API_BASE_URL is unset or invalid; configure it in Vercel settings.');
}
fs.writeFileSync(path.join(dest,'config.js'), 'window.APP_CONFIG = '+JSON.stringify({API_BASE_URL:base.replace(/\/$/,'')})+';\n');
console.log('Static frontend built; backend URL configured:',base ? '(present)' : '(missing)');
