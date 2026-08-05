# Current execution ledger

- [x] item16: Raise upstream CLI feature issue and clean-room pull request
- [x] item17: Tag the experimental high-water mark and rebase onto the clean CLI
- [ ] item18: Run the complete 61-chunk course comparison with stock Ollama and TF (blocked: stock 4K context overflows chunk48)
- [ ] item19: Run the 12-chunk AB/BA quality panel with three judges
- [ ] item20: Publish validation, remove draft status from PR 93, and finalize it

Item18 is blocked after 48 successful TF chunks: the stock 4,096-token context
limit rejected chunk48's 4,673-token prompt. Do not change chunking or pass a
context override without a user decision.
