document.addEventListener('DOMContentLoaded', () => {
    const from = document.querySelector('#from');
    const to = document.querySelector('#to');
    const context = document.querySelector('#context');
    const comment = document.querySelector('#comment');
    document.querySelector('#swapButton')?.addEventListener('click', () => { const value=from.value; from.value=to.value; to.value=value; const fromName=document.querySelector('#from-name'); const toName=document.querySelector('#to-name'); const name=fromName.value; fromName.value=toName.value; toName.value=name; });
    document.querySelector('#generateContext')?.addEventListener('click', async () => {
        const response=await fetch('/generate_context',{method:'POST',body:new URLSearchParams({from:from.value,to:to.value})});
        context.value=(await response.json()).context;
    });
    document.querySelector('#generateComment')?.addEventListener('click', async () => {
        const response=await fetch('/generate_comment',{method:'POST',body:new URLSearchParams({from:from.value,to:to.value,context:context.value})});
        const result=await response.json(); comment.value=result.generated_comment || result.error || '';
    });
});
