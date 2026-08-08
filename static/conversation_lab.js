document.addEventListener('DOMContentLoaded', () => {
    const $ = selector => document.querySelector(selector);
    const windowEl = $('#conversationWindow');
    const selected = id => { const select=$(id); const option=select.options[select.selectedIndex]; return {id:select.value,name:option?.dataset.name || 'Unknown coworker',picture:option?.dataset.picture || ''}; };
    const transcript = () => [...windowEl.querySelectorAll('.message')].map(el => el.innerText).join('\n');
    const appendMessage = (person, text) => {
        windowEl.querySelector('.conversation-empty')?.remove();
        const article=document.createElement('article'); article.className='message';
        const avatar=document.createElement('span'); avatar.className='avatar avatar-sm avatar-tone-'+(Number(person.id)%6); avatar.textContent=person.name.split(/\s+/).map(p=>p[0]).slice(0,2).join('');
        const body=document.createElement('div'); const name=document.createElement('strong'); name.textContent=person.name; const message=document.createElement('p'); message.textContent=text; body.append(name,message); article.append(avatar,body); windowEl.append(article); windowEl.scrollTop=windowEl.scrollHeight;
    };
    const requirePeople = () => { const a=selected('#coworkerA'), b=selected('#coworkerB'); if(!a.id || !b.id){alert('Choose both coworkers first.');return null;} return {a,b}; };
    $('#gptEngine').addEventListener('change', async event => { const response=await fetch('/set_gpt_engine',{method:'POST',body:new URLSearchParams({engine:event.target.value})}); $('#model-state').textContent=response.ok?'Model updated':'Model unavailable'; });
    $('#previewPrompt').addEventListener('click', async () => { const people=requirePeople(); if(!people)return; const response=await fetch('/get_im_prompt_preview',{method:'POST',body:new URLSearchParams({from:people.a.id,to:people.b.id,context:$('#situationContext').value,conversation:transcript()})}); const result=await response.json(); $('.prompt-field').hidden=false; $('#gptPrompt').value=result.prompt || result.error || ''; });
    const generate = async side => { const people=requirePeople(); if(!people)return; const speaker=side==='A'?people.a:people.b; const other=side==='A'?people.b:people.a; const button=$(`#simulateReply${side}`); button.disabled=true; button.textContent='Thinking…'; try { const response=await fetch('/generate_im_message',{method:'POST',body:new URLSearchParams({from:speaker.id,to:other.id,context:$('#situationContext').value,conversation:transcript(),custom_prompt:$('#gptPrompt').value})}); const result=await response.json(); appendMessage(speaker,result.generated_message || result.error || 'No response.'); } finally { button.disabled=false; button.textContent=`Generate as ${side}`; } };
    $('#simulateReplyA').addEventListener('click',()=>generate('A')); $('#simulateReplyB').addEventListener('click',()=>generate('B'));
    $('#sendManualMessage').addEventListener('click',()=>{const people=requirePeople();if(!people)return;const text=$('#manualMessage').value.trim();if(!text)return;appendMessage($('#manualSender').value==='A'?people.a:people.b,text);$('#manualMessage').value='';});
    $('#manualMessage').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('#sendManualMessage').click();}});
    $('#clearConversation').addEventListener('click',()=>{windowEl.innerHTML='<div class="conversation-empty"><span>OT</span><h2>Start the simulation</h2><p>Select two coworkers and give them something to talk about.</p></div>';});
});
