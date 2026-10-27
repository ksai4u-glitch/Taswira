const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawnSync}=require('node:child_process');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'taswira-capture-test-'));
try{
  const output=path.join(directory,'failed.mp4');
  const result=spawnSync(process.execPath,[path.join(__dirname,'..','capture_history.cjs'),process.argv[2],process.argv[3],output,'1','1'],
    {env:{...process.env,FFMPEG_PATH:path.join(directory,'missing-ffmpeg')},encoding:'utf8',timeout:15000});
  assert.notEqual(result.error?.code,'ETIMEDOUT','A missing encoder must fail promptly, not wait forever for drain');
  assert.equal(result.status,1);assert.equal(fs.existsSync(output),false);
  assert.equal(fs.existsSync(output.replace('.mp4','.vtt')),false);
  assert.equal(fs.existsSync(output.replace('.mp4','.sources.json')),false);
  assert.deepEqual(fs.readdirSync(directory),[],'Failed captures must clean temporary output');
  fs.writeFileSync(output,'existing video sentinel');
  const existing=spawnSync(process.execPath,[path.join(__dirname,'..','capture_history.cjs'),process.argv[2],process.argv[3],output,'1','1'],{encoding:'utf8',timeout:5000});
  assert.equal(existing.status,1);assert.equal(fs.readFileSync(output,'utf8'),'existing video sentinel');
  console.log('PASS: missing encoder exits promptly, leaves no partial video, sidecars or temporary files.');
}finally{fs.rmSync(directory,{recursive:true,force:true});}
