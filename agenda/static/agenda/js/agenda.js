// Agenda JavaScript - Gerenciamento de Modais e Funcionalidades
const _agendaBody = document.body;
window.AGENDA_CURRENT_DATE = _agendaBody.dataset.currentDate || '';
window.AGENDA_VIEW_TYPE    = _agendaBody.dataset.viewType    || 'semana';
window.produtosEstoque     = JSON.parse(_agendaBody.dataset.produtos || '[]');

document.addEventListener('DOMContentLoaded', function () {
    // Aplicar cor de borda nos cards do mês via data-cor
    document.querySelectorAll('.month-event-item[data-cor]').forEach(el => {
        el.style.setProperty('--card-cor', el.dataset.cor);
    });
    // Redirecionamento automático para visualização "dia" no mobile se não houver parâmetro explícito
    const urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('view') && window.innerWidth <= 768) {
        if (window.AGENDA_VIEW_TYPE !== 'dia') {
            urlParams.set('view', 'dia');
            window.location.search = urlParams.toString();
            return;
        }
    }

    // ========== MODAL NOVO AGENDAMENTO ==========
    const modal = document.getElementById('modal-agendamento');
    const btnNew = document.getElementById('btn-new-appointment');
    const btnClose = document.getElementById('btn-close-modal');
    const btnCancel = document.getElementById('btn-cancel-modal');

    function openModal() {
        modal.classList.add('active');
    }

    function closeModal() {
        modal.classList.remove('active');
    }

    if (btnNew) btnNew.addEventListener('click', openModal);
    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (btnCancel) btnCancel.addEventListener('click', closeModal);

    // Character counter for observacoes (novo agendamento)
    const obsTextarea = document.getElementById('id_observacoes');
    const obsCounter = document.getElementById('obs-counter');
    if (obsTextarea && obsCounter) {
        obsTextarea.addEventListener('input', function () {
            obsCounter.textContent = `${this.value.length}/70`;
        });
    }

    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    // ========== MODAL EDITAR AGENDAMENTO ==========
    const modalEditar = document.getElementById('modal-editar-agendamento');
    const btnCloseEditar = document.getElementById('btn-close-modal-editar');
    const btnCancelEditar = document.getElementById('btn-cancel-modal-editar');
    const btnDelete = document.getElementById('btn-delete-agendamento');
    const formEditar = document.getElementById('form-editar-agendamento');
    let currentAgendamentoId = null;

    function openModalEditar() {
        if (!modalEditar) return;
        modalEditar.classList.add('active');
    }

    function closeModalEditar() {
        modalEditar.classList.remove('active');
        currentAgendamentoId = null;
    }

    if (btnCloseEditar) btnCloseEditar.addEventListener('click', closeModalEditar);
    if (btnCancelEditar) btnCancelEditar.addEventListener('click', closeModalEditar);

    // Character counter for observacoes (editar agendamento)
    const editObsTextarea = document.getElementById('edit_observacoes');
    const editObsCounter = document.getElementById('edit-obs-counter');
    if (editObsTextarea && editObsCounter) {
        editObsTextarea.addEventListener('input', function () {
            editObsCounter.textContent = `${this.value.length}/70`;
        });
    }

    modalEditar.addEventListener('click', function (e) {
        if (e.target === modalEditar) {
            closeModalEditar();
        }
    });

    // Click nos cards de agendamento (desktop)
    document.addEventListener('click', function (e) {
        const card = e.target.closest('.event-card-clickable');
        if (card) {
            const agendamentoId = card.dataset.id;
            const isFinalizado = card.classList.contains('event-finalizado');
            openModalDetalhes(agendamentoId, isFinalizado);
        }
    });

    // Botão "Sincronizar agora" com o Google Calendar
    const btnSincronizarGoogle = document.getElementById('btn-sincronizar-google');
    if (btnSincronizarGoogle) {
        btnSincronizarGoogle.addEventListener('click', function () {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const iconEl = btnSincronizarGoogle.querySelector('i');
            btnSincronizarGoogle.disabled = true;
            if (iconEl) iconEl.classList.add('fa-spin');

            fetch('/agenda/sincronizar/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert(data.error || 'Não foi possível sincronizar com o Google.');
                        btnSincronizarGoogle.disabled = false;
                        if (iconEl) iconEl.classList.remove('fa-spin');
                    }
                })
                .catch(() => {
                    alert('Não foi possível sincronizar com o Google.');
                    btnSincronizarGoogle.disabled = false;
                    if (iconEl) iconEl.classList.remove('fa-spin');
                });
        });
    }


    // Botão de status (toggle Pendente / Aguardando — amarelo nos cards)
    const btnStatus = document.getElementById('btn-details-status');
    const btnStatusLabel = document.getElementById('btn-details-status-label');
    let currentStatus = 'Pendente';

    if (btnStatus) {
        btnStatus.addEventListener('click', function () {
            if (!currentAgendamentoId) return;

            const novoStatus = currentStatus === 'Aguardando' ? 'Pendente' : 'Aguardando';
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/agenda/status/${currentAgendamentoId}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ status: novoStatus }),
            })
                .then(r => r.json())
                .then(data => {
                    if (!data.success) return;
                    currentStatus = novoStatus;
                    _updateStatusBtn(novoStatus);

                    // Atualizar todos os cards com este id (mês + semana/dia)
                    document.querySelectorAll(`[data-id="${currentAgendamentoId}"]`).forEach(card => {
                        card.dataset.status = novoStatus;
                        if (novoStatus === 'Aguardando') {
                            card.style.setProperty('border-left-color', '#ff0000', 'important');
                            card.style.setProperty('background', 'rgba(255, 0, 0, 0.12)', 'important');
                        } else {
                            card.style.removeProperty('border-left-color');
                            card.style.removeProperty('background');
                        }
                    });
                });
        });
    }

    function _updateStatusBtn(status) {
        if (!btnStatus || !btnStatusLabel) return;
        const isAguardando = status === 'Aguardando';
        btnStatusLabel.textContent = isAguardando ? 'MARCAR COMO NÃO VISTO' : 'MARCAR COMO VISTO';
        btnStatus.classList.toggle('ativo', isAguardando);
    }

    // Abrir o novo modal de 'Detalhes do Agendamento'
    function openModalDetalhes(agendamentoId, isFinalizado) {
        currentAgendamentoId = agendamentoId;

        const botoes = document.getElementById('detalhes_acoes_botoes');
        const aviso = document.getElementById('detalhes_acoes_aviso');

        if (botoes && aviso) {
            botoes.style.display = isFinalizado ? 'none' : 'flex';
            aviso.style.display = isFinalizado ? 'flex' : 'none';
        }

        // Inicializar status a partir do card existente no DOM
        const anyCard = document.querySelector(`[data-id="${agendamentoId}"]`);
        currentStatus = anyCard ? (anyCard.dataset.status || 'Pendente') : 'Pendente';
        _updateStatusBtn(currentStatus);
        
        fetch(`/agenda/editar/${agendamentoId}/`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => {
                document.getElementById('visualizar_cliente_nome').textContent = data.cliente_nome || 'Não informado';

                const elTelefone = document.getElementById('visualizar_telefone');
                if (elTelefone) elTelefone.textContent = data.cliente_telefone || 'Não informado';

                const elDataHora = document.getElementById('visualizar_data_horario_display');
                if (elDataHora) elDataHora.textContent = data.data_horario_display || '';

                const elDuracao = document.getElementById('visualizar_duracao');
                if (elDuracao) elDuracao.textContent = data.duracao ? `${data.duracao} min` : '';

                const elObs = document.getElementById('visualizar_observacoes');
                if (elObs) elObs.textContent = data.observacoes || '';
                const elObsRow = document.getElementById('visualizar_observacoes_row');
                if (elObsRow) elObsRow.style.display = data.observacoes ? '' : 'none';

                // Preencher serviços e produtos realizados no aviso de finalizado
                const elServicosRealizados = document.getElementById('detalhes_servicos_realizados');
                if (elServicosRealizados) {
                    const servicos = data.servicos_realizados || [];
                    const produtos = data.produtos_realizados || [];
                    let html = '';

                    if (servicos.length > 0) {
                        html += `
                            <p style="font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 0.5px;">Serviços Realizados</p>
                            <ul style="list-style: none; padding: 0; margin: 0 0 12px 0; display: flex; flex-direction: column; gap: 6px;">
                                ${servicos.map(s => `
                                    <li style="display: flex; align-items: center; gap: 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; font-size: 13px; color: var(--text-primary);">
                                        <i class="fas fa-scissors" style="color: #22a064; font-size: 12px; flex-shrink: 0;"></i>
                                        <span>${s.servico || s.tipo || 'Serviço'}</span>
                                    </li>
                                `).join('')}
                            </ul>`;
                    }

                    if (produtos.length > 0) {
                        html += `
                            <p style="font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 0.5px;">Produtos Vendidos</p>
                            <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px;">
                                ${produtos.map(p => `
                                    <li style="display: flex; align-items: center; gap: 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; font-size: 13px; color: var(--text-primary);">
                                        <i class="fas fa-shopping-bag" style="color: #2563eb; font-size: 12px; flex-shrink: 0;"></i>
                                        <span>${p.nome || 'Produto'} ${p.quantidade > 1 ? `<span style="color: var(--text-muted);">x${p.quantidade}</span>` : ''}</span>
                                    </li>
                                `).join('')}
                            </ul>`;
                    }

                    elServicosRealizados.innerHTML = html;
                }

                document.getElementById('modal-visualizar-atendimento').classList.add('active');
            })
            .catch(error => {
                console.error('Erro ao carregar detalhes do agendamento:', error);
                alert('Erro ao carregar dados do agendamento');
            });
    }

    // Carregar dados do agendamento
    function loadAgendamento(id) {
        currentAgendamentoId = id;
        fetch(`/agenda/editar/${id}/`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => {
                const editClienteSearch = document.getElementById('edit_cliente_search');
                const editClienteTelefone = document.getElementById('edit_cliente_telefone');
                if (editClienteSearch) editClienteSearch.value = data.cliente_nome || '';
                if (editClienteTelefone) editClienteTelefone.value = data.cliente_telefone || '';

                const elDataHorario = document.getElementById('edit_data_horario');
                if (elDataHorario) elDataHorario.value = data.data_horario;
                const elDuracao = document.getElementById('edit_duracao');
                if (elDuracao) elDuracao.value = data.duracao;
                const elCor = document.getElementById('edit_cor');
                if (elCor) elCor.value = data.cor || '#ff0000';
                const editObs = document.getElementById('edit_observacoes');
                if (editObs) editObs.value = data.observacoes || '';
                const editObsCounter = document.getElementById('edit-obs-counter');
                if (editObsCounter) editObsCounter.textContent = `${(data.observacoes || '').length}/70`;

                // Atualizar action do formulário
                if (formEditar) formEditar.action = `/agenda/editar/${id}/`;

                openModalEditar();
            })
            .catch(error => {
                console.error('Erro ao carregar agendamento:', error);
                alert(`Erro ao carregar dados do agendamento: ${error.message}`);
            });
    }

    // Excluir agendamento
    if (btnDelete) {
        btnDelete.addEventListener('click', function () {
            if (confirm('Tem certeza que deseja excluir este agendamento?')) {
                const formDelete = document.createElement('form');
                formDelete.method = 'POST';
                formDelete.action = `/agenda/excluir/${currentAgendamentoId}/`;

                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                formDelete.appendChild(csrfInput);

                const redirectData = document.createElement('input');
                redirectData.type = 'hidden';
                redirectData.name = 'redirect_data';
                redirectData.value = window.AGENDA_CURRENT_DATE || '';
                formDelete.appendChild(redirectData);

                const redirectView = document.createElement('input');
                redirectView.type = 'hidden';
                redirectView.name = 'redirect_view';
                redirectView.value = window.AGENDA_VIEW_TYPE || 'semana';
                formDelete.appendChild(redirectView);

                document.body.appendChild(formDelete);
                formDelete.submit();
            }
        });
    }

    // O autocomplete de cliente é tratado pela seção de autocomplete abaixo.

    // ========== MODAL FINALIZAR ATENDIMENTO ==========
    const modalFinalizar = document.getElementById('modal-finalizar-atendimento');
    const btnCloseFinalizar = document.getElementById('btn-close-modal-finalizar');
    const btnCancelFinalizar = document.getElementById('btn-cancel-modal-finalizar');
    const formFinalizar = document.getElementById('form-finalizar-atendimento');

    // Tab switching functionality
    document.addEventListener('click', function (e) {
        const tabBtn = e.target.closest('.tab-btn');
        if (tabBtn) {
            const tabName = tabBtn.getAttribute('data-tab');

            // Update button styles
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.style.background = '#f0f0f0';
            });
            tabBtn.style.background = '#c5e1a5';

            // Show/hide content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.querySelector(`.tab-content[data-content="${tabName}"]`).style.display = 'block';
        }
    });

    function openModalFinalizar(agendamentoId) {
        if (!modalFinalizar) {
            window.location.href = `/agenda/finalizar-mobile/${agendamentoId}/`;
            return;
        }
        // Buscar dados do agendamento via AJAX
        fetch(`/agenda/get/${agendamentoId}/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('finalizar_agendamento_id').value = data.id;
                document.getElementById('finalizar_cliente_nome').value = data.cliente_nome;
                document.getElementById('finalizar_cliente_nome_display').textContent = data.cliente_nome;

                // Preencher estatísticas do cliente
                const telefoneEl = document.getElementById('cliente_telefone');
                if (telefoneEl) {
                    telefoneEl.textContent = data.cliente_telefone || 'N/A';
                }

                const clienteDesdeEl = document.getElementById('cliente_desde');
                if (clienteDesdeEl) {
                    clienteDesdeEl.textContent = data.cliente_desde || 'N/A';
                }

                const ultimaVisitaEl = document.getElementById('ultima_visita');
                if (ultimaVisitaEl) {
                    ultimaVisitaEl.textContent = data.ultima_visita || 'Primeira visita';
                }

                modalFinalizar.classList.add('active');
                calcularTotalFinalizar();
            })
            .catch(error => {
                console.error('Erro ao carregar agendamento:', error);
                alert('Erro ao carregar dados do agendamento');
            });
    }

    function closeModalFinalizar() {
        if (!modalFinalizar) return;
        modalFinalizar.classList.remove('active');
        formFinalizar.reset();

        // Resetar inputs de pagamento (desabilitar novamente)
        const inputsPagamento = formFinalizar.querySelectorAll('.input-valor-forma');
        inputsPagamento.forEach(input => {
            input.disabled = true;
            input.style.opacity = '0.4';
        });

        // Limpar serviços adicionais
        const container = document.getElementById('finalizar-servicos-container');
        const servicosAdicionais = container.querySelectorAll('.servico-item[data-index]:not([data-index="0"])');
        servicosAdicionais.forEach(item => item.remove());
        // Limpar produtos adicionais
        const containerProdutos = document.getElementById('finalizar-produtos-container');
        const produtosAdicionais = containerProdutos.querySelectorAll('.produto-item[data-index]:not([data-index="0"])');
        produtosAdicionais.forEach(item => item.remove());
        servicoIndexFinalizar = 1;
        produtoIndexFinalizar = 1;
        calcularTotalFinalizar();
    }

    if (btnCloseFinalizar) btnCloseFinalizar.addEventListener('click', closeModalFinalizar);
    if (btnCancelFinalizar) btnCancelFinalizar.addEventListener('click', closeModalFinalizar);

    if (modalFinalizar) modalFinalizar.addEventListener('click', function (e) {
        if (e.target === modalFinalizar) {
            closeModalFinalizar();
        }
    });

    // Botões de ação do Modal de Detalhes
    document.addEventListener('click', function (e) {
        // TROCAR CLIENTE
        if (e.target.closest('#btn-details-change-client')) {
            e.preventDefault();
            closeModalVisualizar();
            if (currentAgendamentoId) loadAgendamento(currentAgendamentoId);
        }

        // FINALIZAR AGENDAMENTO
        if (e.target.closest('#btn-details-finalize')) {
            e.preventDefault();
            closeModalVisualizar();
            if (currentAgendamentoId) openModalFinalizar(currentAgendamentoId);
        }

        // REMARCAR AGENDAMENTO
        if (e.target.closest('#btn-details-reschedule')) {
            e.preventDefault();
            closeModalVisualizar();
            if (currentAgendamentoId) loadAgendamento(currentAgendamentoId);
        }

        // CANCELAR AGENDAMENTO
        if (e.target.closest('#btn-details-cancel')) {
            e.preventDefault();
            if (confirm('Tem certeza que deseja cancelar (excluir) este agendamento?')) {
                const formDelete = document.createElement('form');
                formDelete.method = 'POST';
                formDelete.action = `/agenda/excluir/${currentAgendamentoId}/`;

                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                formDelete.appendChild(csrfInput);

                const redirectData = document.createElement('input');
                redirectData.type = 'hidden';
                redirectData.name = 'redirect_data';
                redirectData.value = window.AGENDA_CURRENT_DATE || '';
                formDelete.appendChild(redirectData);

                const redirectView = document.createElement('input');
                redirectView.type = 'hidden';
                redirectView.name = 'redirect_view';
                redirectView.value = window.AGENDA_VIEW_TYPE || 'semana';
                formDelete.appendChild(redirectView);

                document.body.appendChild(formDelete);
                formDelete.submit();
            }
        }
    });

    // ========== FUNCIONALIDADE DE MÚLTIPLOS SERVIÇOS ==========
    let servicoIndexFinalizar = 1;
    const btnAddServicoFinalizar = document.getElementById('btn-add-servico-finalizar');
    const servicosContainerFinalizar = document.getElementById('finalizar-servicos-container');

    // Adicionar novo serviço
    if (btnAddServicoFinalizar) {
        btnAddServicoFinalizar.addEventListener('click', function () {
            const idx = servicoIndexFinalizar;
            const newServicoItem = document.createElement('div');
            newServicoItem.className = 'servico-item';
            newServicoItem.setAttribute('data-index', idx);
            newServicoItem.style.cssText = 'padding: 8px 0; border-bottom: 1px solid var(--border); margin-bottom: 6px;';

            newServicoItem.innerHTML = `
                <div class="servico-row-grid" style="display: grid; grid-template-columns: 140px 1fr 110px 90px 36px; gap: 10px; align-items: center;">
                    <div class="servico-col-tipo">
                        <select name="servico_tipo_${idx}" class="form-control" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; background: var(--bg); color: var(--text-primary); font-size: 13px;">
                            <option value="" disabled selected>Selecionar...</option>
                            <option value="Corte">Corte</option>
                            <option value="Coloração">Coloração</option>
                            <option value="Camuflagem Gloss">Camuflagem Gloss</option>
                            <option value="Luzes">Luzes</option>
                            <option value="Relaxamento">Relaxamento</option>
                            <option value="Manicure">Manicure</option>
                            <option value="Pedicure">Pedicure</option>
                            <option value="Pedicure e Manicure">Pedicure e Manicure</option>
                            <option value="Alisamento">Alisamento</option>
                            <option value="Penteado">Penteado</option>
                            <option value="Escova">Escova</option>
                            <option value="Tratamento Capilar">Tratamento Capilar</option>
                            <option value="Sobrancelha e Buço">Sobrancelha e Buço</option>
                            <option value="Maquiagem">Maquiagem</option>
                            <option value="Sobrancelha">Sobrancelha</option>
                            <option value="Outro">Não especificado</option>
                        </select>
                    </div>
                    <div class="servico-col-nome">
                        <input type="text" name="servico_${idx}" class="form-control" placeholder="Ex: Corte feminino" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px; background: var(--bg); color: var(--text-primary);">
                    </div>
                    <div class="servico-col-valor">
                        <input type="number" name="valor_servico_${idx}" class="form-control valor-servico-finalizar" min="0" step="0.01" placeholder="0,00" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px; text-align: right; background: var(--bg); color: var(--text-primary);">
                    </div>
                    <div class="servico-col-desc">
                        <input type="number" name="desconto_servico_${idx}" class="form-control desconto-servico-finalizar" min="0" step="0.01" placeholder="0,00" value="0" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px; text-align: right; background: var(--bg); color: var(--text-primary);">
                    </div>
                    <div class="servico-col-rm">
                        <button type="button" class="btn-remove-servico" data-index="${idx}" style="background: none; border: none; color: #dc3545; cursor: pointer; font-size: 16px; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center;" title="Remover">
                            <i class="fas fa-times-circle"></i>
                        </button>
                    </div>
                </div>
            `;

            servicosContainerFinalizar.appendChild(newServicoItem);
            servicoIndexFinalizar++;

            // Adicionar event listeners
            const newValorInput = newServicoItem.querySelector('.valor-servico-finalizar');
            const newDescontoInput = newServicoItem.querySelector('.desconto-servico-finalizar');
            if (newValorInput) newValorInput.addEventListener('input', calcularTotalFinalizar);
            if (newDescontoInput) newDescontoInput.addEventListener('input', calcularTotalFinalizar);
        });
    }

    // Remover serviço
    if (servicosContainerFinalizar) servicosContainerFinalizar.addEventListener('click', function (e) {
        const btnRemove = e.target.closest('.btn-remove-servico');
        if (btnRemove) {
            const index = btnRemove.getAttribute('data-index');
            const servicoItem = servicosContainerFinalizar.querySelector(`[data-index="${index}"]`);
            if (servicoItem) {
                servicoItem.remove();
                calcularTotalFinalizar();
            }
        }
    });

    // Autocomplete de Produtos reutilizável para novas linhas e modal
    function setupProdutoAutocomplete(containerEl) {
        const searchInput = containerEl.querySelector('.produto-search');
        const hiddenId = containerEl.querySelector('.produto-hidden');
        const list = containerEl.querySelector('.produto-autocomplete-list');
        
        if (!searchInput || !hiddenId || !list) return;

        searchInput.addEventListener('input', function () {
            hiddenId.value = '';   // Invalida seleção se usuário alterar texto livre
            const q = this.value.trim().toLowerCase();
            
            if (q.length < 1) { 
                closeList(); 
                return; 
            }

            const produtos = (window.produtosEstoque || []).filter(p => p.nome.toLowerCase().includes(q));
            renderList(produtos);
        });

        searchInput.addEventListener('focus', function() {
            if (this.value.trim().length === 0) {
                renderList(window.produtosEstoque || []);
            } else {
                 const q = this.value.trim().toLowerCase();
                 const produtos = (window.produtosEstoque || []).filter(p => p.nome.toLowerCase().includes(q));
                 renderList(produtos);
            }
        });

        function renderList(produtos) {
            list.innerHTML = '';
            if (!produtos.length) { 
                const li = document.createElement('li');
                li.style.cssText = 'padding:10px 14px;color:var(--text-muted);font-size:12px;';
                li.textContent = 'Nenhum produto encontrado no estoque (qtd > 0)';
                list.appendChild(li);
                list.style.display = 'block';
                return; 
            }

            produtos.forEach(p => {
                const li = document.createElement('li');
                li.style.cssText = 'padding:10px 14px;cursor:pointer;display:flex;justify-content:space-between;border-bottom:1px solid var(--border);transition:background 0.15s;color:var(--text-primary);';
                li.innerHTML = `<span style="font-weight:500;">${p.nome}</span><span style="font-size:12px;color:var(--text-muted);">R$ ${p.preco.toFixed(2)}</span>`;
                
                li.addEventListener('mouseenter', () => li.style.background = 'var(--surface)');
                li.addEventListener('mouseleave', () => li.style.background = '');
                li.addEventListener('mousedown', e => { 
                    e.preventDefault(); 
                    selectProduto(p.nome, p.preco); 
                });
                
                list.appendChild(li);
            });
            list.style.display = 'block';
        }

        function selectProduto(nome, preco) {
            hiddenId.value = nome;
            searchInput.value = nome;
            closeList();
            
            const itemVenda = containerEl.closest('.produto-item');
            if (itemVenda) {
                const inputValor = itemVenda.querySelector('.valor-produto-finalizar');
                if (inputValor) {
                    inputValor.value = preco.toFixed(2);
                    inputValor.dispatchEvent(new Event('input')); // Recalcula subtotal
                }
            }
        }

        function closeList() {
            list.style.display = 'none';
            list.innerHTML = '';
        }

        document.addEventListener('click', e => {
            if (!searchInput.contains(e.target) && !list.contains(e.target)) closeList();
        });
    }

    // Inicializa item 0 se existir
    const produtoZeroContainer = document.getElementById('finalizar-produtos-container');
    if (produtoZeroContainer) {
        const itemZero = produtoZeroContainer.querySelector('.produto-item[data-index="0"]');
        if (itemZero) {
            setupProdutoAutocomplete(itemZero.querySelector('.produto-autocomplete-container'));
        }
    }

    // ========== FUNCIONALIDADE DE MÚLTIPLOS PRODUTOS ==========
    let produtoIndexFinalizar = 1;
    const btnAddProdutoFinalizar = document.getElementById('btn-add-produto-finalizar');
    const produtosContainerFinalizar = document.getElementById('finalizar-produtos-container');

    // Adicionar novo produto
    if (btnAddProdutoFinalizar) {
        btnAddProdutoFinalizar.addEventListener('click', function () {
            const newProdutoItem = document.createElement('div');
            newProdutoItem.className = 'produto-item';
            newProdutoItem.setAttribute('data-index', produtoIndexFinalizar);
            newProdutoItem.style.cssText = 'background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;';
            newProdutoItem.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 70px 110px 90px 36px; gap: 10px; align-items: center;">
                    <div class="produto-autocomplete-container" style="position: relative;">
                        <input type="text" class="produto-search form-control" placeholder="Buscar produto..." autocomplete="off" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px;">
                        <input type="hidden" name="produto_${produtoIndexFinalizar}" class="produto-hidden">
                        <ul class="produto-autocomplete-list" style="
                            display: none;
                            position: absolute;
                            top: 100%;
                            left: 0;
                            right: 0;
                            z-index: 9999;
                            background: var(--bg);
                            border: 1px solid var(--border);
                            border-radius: 0 0 8px 8px;
                            margin: 0;
                            padding: 0;
                            list-style: none;
                            box-shadow: 0 4px 12px var(--shadow);
                            max-height: 220px;
                            overflow-y: auto;
                            font-size: 13px;
                        "></ul>
                    </div>
                    <input type="number" name="qtd_produto_${produtoIndexFinalizar}"
                        class="form-control qtd-produto-finalizar" min="1" step="1" value="1" placeholder="1" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px;">
                    <input type="number" name="valor_produto_${produtoIndexFinalizar}"
                        class="form-control valor-produto-finalizar" min="0" step="0.01"
                        placeholder="0,00" readonly style="background: var(--bg2); border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px;">
                    <input type="number" name="desconto_produto_${produtoIndexFinalizar}" class="form-control desconto-produto-finalizar" 
                        min="0" step="0.01" placeholder="0,00" value="0" style="border: 1px solid var(--border); padding: 7px 8px; border-radius: 6px; width: 100%; font-size: 13px;">
                    <button type="button" class="btn-remove-produto" data-index="${produtoIndexFinalizar}" style="background: none; border: none; color: #dc3545; cursor: pointer; font-size: 16px; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-times-circle"></i>
                    </button>
                </div>
            `;
            produtosContainerFinalizar.appendChild(newProdutoItem);
            
            // Inicializa o autocomplete no item que acabou de ser adicionado
            setupProdutoAutocomplete(newProdutoItem.querySelector('.produto-autocomplete-container'));
            produtoIndexFinalizar++;

            // Adicionar event listeners
            const newQtdInput = newProdutoItem.querySelector('.qtd-produto-finalizar');
            const newValorInput = newProdutoItem.querySelector('.valor-produto-finalizar');
            const newDescontoInput = newProdutoItem.querySelector('.desconto-produto-finalizar');
            if (newQtdInput) newQtdInput.addEventListener('input', calcularTotalFinalizar);
            if (newValorInput) newValorInput.addEventListener('input', calcularTotalFinalizar);
            if (newDescontoInput) newDescontoInput.addEventListener('input', calcularTotalFinalizar);
        });
    }

    // Remover produto
    if (produtosContainerFinalizar) produtosContainerFinalizar.addEventListener('click', function (e) {
        const btnRemove = e.target.closest('.btn-remove-produto');
        if (btnRemove) {
            const index = btnRemove.getAttribute('data-index');
            const produtoItem = produtosContainerFinalizar.querySelector(`.produto-item[data-index="${index}"]`);
            if (produtoItem) {
                produtoItem.remove();
                calcularTotalFinalizar();
            }
        }
    });

    // ========== FUNCIONALIDADE DE MÚLTIPLOS PAGAMENTOS ==========
    // Renderiza inputs de pagamento caso não venham do Python
    const pagamentosLista = document.getElementById('formas-pagamento-lista');
    if (pagamentosLista) {
        // Se a lista estiver vazia (sem checkboxes renderizados pelo Django), renderiza via JS
        if (pagamentosLista.querySelectorAll('.chk-forma-pagamento').length === 0) {
            const formas = [
                ['pix', 'PIX'],
                ['credito', 'Crédito'],
                ['debito', 'Débito'],
                ['dinheiro', 'Dinheiro'],
                ['transferencia', 'Transação Bancária'],
                ['outros', 'Outros'],
            ];
            formas.forEach(([val, label]) => {
                const row = document.createElement('div');
                row.style.cssText = 'display:flex;align-items:center;gap:10px;';
                row.innerHTML = `
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px;color:#555;min-width:140px;">
                    <input type="checkbox" name="forma_pagamento" value="${val}" class="chk-forma-pagamento" style="width:16px;height:16px;">
                    ${label}
                </label>
                <input type="number" name="valor_forma_${val}" class="input-valor-forma" data-forma="${val}"
                    min="0" step="0.01" placeholder="R$ 0,00" disabled
                    style="width:110px;padding:6px 8px;border:1px solid #ddd;border-radius:6px;font-size:13px;opacity:0.4;transition:opacity 0.2s;">
            `;
                pagamentosLista.appendChild(row);
            });
        }

        // Event listeners para a lista de pagamentos
        pagamentosLista.addEventListener('change', function (e) {
            if (e.target.classList.contains('chk-forma-pagamento')) {
                const row = e.target.closest('div');
                const input = row.querySelector('.input-valor-forma');
                if (e.target.checked) {
                    input.disabled = false;
                    input.style.opacity = '1';
                    input.focus();
                } else {
                    input.disabled = true;
                    input.value = '';
                    input.style.opacity = '0.4';
                }
                calcularTotalFinalizar();
            }
        });

        pagamentosLista.addEventListener('input', function (e) {
            if (e.target.classList.contains('input-valor-forma')) {
                calcularTotalFinalizar();
            }
        });
    }

    // ========== CALCULAR TOTAL COM DESCONTOS ==========
    function calcularTotalFinalizar() {
        let total = 0;

        // Somar serviços (valor - desconto)
        const servicosItems = document.querySelectorAll('.servico-item');
        servicosItems.forEach(item => {
            const valorInput = item.querySelector('.valor-servico-finalizar');
            const descontoInput = item.querySelector('.desconto-servico-finalizar');
            if (valorInput) {
                const valor = parseFloat(valorInput.value) || 0;
                const desconto = descontoInput ? (parseFloat(descontoInput.value) || 0) : 0;
                const valorFinal = Math.max(0, valor - desconto);
                total += valorFinal;

                // Atualizar valor final exibido no item
                const valorFinalSpan = item.querySelector('.valor-final-servico');
                if (valorFinalSpan) {
                    valorFinalSpan.textContent = valorFinal.toFixed(2).replace('.', ',');
                }
            }
        });

        // Somar produtos (quantidade * valor - desconto)
        const produtosItems = document.querySelectorAll('.produto-item');
        produtosItems.forEach(item => {
            const qtdInput = item.querySelector('.qtd-produto-finalizar');
            const valorInput = item.querySelector('.valor-produto-finalizar');
            const descontoInput = item.querySelector('.desconto-produto-finalizar');
            if (qtdInput && valorInput) {
                const qtd = parseInt(qtdInput.value) || 0;
                const valor = parseFloat(valorInput.value) || 0;
                const desconto = descontoInput ? (parseFloat(descontoInput.value) || 0) : 0;
                const valorFinal = Math.max(0, (qtd * valor) - desconto);
                total += valorFinal;

                // Atualizar valor final exibido no item
                const valorFinalSpan = item.querySelector('.valor-final-produto');
                if (valorFinalSpan) {
                    valorFinalSpan.textContent = valorFinal.toFixed(2).replace('.', ',');
                }
            }
        });

        // Atualizar displays de TOTAL GERAL
        const totalFormatado = total.toFixed(2).replace('.', ',');
        const totalEl = document.getElementById('total-valor-finalizar');
        const resumoTotalEl = document.getElementById('resumo-total');
        if (totalEl) totalEl.textContent = totalFormatado;
        if (resumoTotalEl) resumoTotalEl.textContent = totalFormatado;

        // Calcular e atualizar RECEBIDO e FALTA com base nos inputs de métodos de pagamento
        let recebido = 0;
        const inputsPagamento = document.querySelectorAll('.input-valor-forma:not([disabled])');
        inputsPagamento.forEach(inp => {
            recebido += parseFloat(inp.value) || 0;
        });

        const falta = Math.max(0, total - recebido);

        const recebidoEl = document.getElementById('resumo-recebido');
        const faltaEl = document.getElementById('resumo-falta');
        if (recebidoEl) recebidoEl.textContent = recebido.toFixed(2).replace('.', ',');
        if (faltaEl) faltaEl.textContent = falta.toFixed(2).replace('.', ',');
    }

    // Adicionar event listeners para campos de serviço/produto existentes
    document.querySelectorAll('.valor-servico-finalizar, .desconto-servico-finalizar').forEach(input => {
        input.addEventListener('input', calcularTotalFinalizar);
    });

    document.querySelectorAll('.qtd-produto-finalizar, .valor-produto-finalizar, .desconto-produto-finalizar').forEach(input => {
        input.addEventListener('input', calcularTotalFinalizar);
    });

    // ========== SUBMIT DO FORMULÁRIO DE FINALIZAÇÃO ==========
    if (formFinalizar) {
        formFinalizar.addEventListener('submit', function (e) {
            e.preventDefault();

            const temServico = document.querySelector('#finalizar-servicos-container input[name^="servico_"]')?.value?.trim();
            const temProduto = document.querySelector('#finalizar-produtos-container input[name^="produto_"]')?.value?.trim();
            if (!temServico && !temProduto) {
                alert('Informe ao menos um serviço ou produto para finalizar o atendimento.');
                return;
            }

            const agendamentoId = document.getElementById('finalizar_agendamento_id').value;
            const formData = new FormData(formFinalizar);

            fetch(`/agenda/finalizar/${agendamentoId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const msg = `Atendimento finalizado! ${data.servicos_criados} serviço(s) e ${data.produtos_criados} produto(s) registrado(s).`;
                        alert(msg);
                        closeModalFinalizar();
                        location.reload(); // Recarregar página para atualizar calendário
                    } else {
                        alert('Erro ao finalizar atendimento: ' + (data.error || 'Erro desconhecido'));
                    }
                })
                .catch(error => {
                    console.error('Erro ao finalizar atendimento:', error);
                    alert('Erro ao finalizar atendimento. Verifique o console para mais detalhes.');
                });
        });
    }

    // ========== MODAL VISUALIZAR ATENDIMENTO ==========
    const modalVisualizar = document.getElementById('modal-visualizar-atendimento');
    const btnCloseVisualizar = document.getElementById('btn-close-modal-visualizar');

    function closeModalVisualizar() {
        modalVisualizar.classList.remove('active');
    }

    if (btnCloseVisualizar) btnCloseVisualizar.addEventListener('click', closeModalVisualizar);

    if (modalVisualizar) {
        modalVisualizar.addEventListener('click', function (e) {
            if (e.target === modalVisualizar) {
                closeModalVisualizar();
            }
        });
    }

    // ========== AUTOCOMPLETE DE CLIENTE (NOVO AGENDAMENTO) ==========
    (function () {
        const searchInput = document.getElementById('cliente-search');
        const telefoneInput = document.getElementById('cliente-telefone');
        const list = document.getElementById('cliente-autocomplete-list');
        if (!searchInput || !list) return;

        let debounceTimer = null;
        let selectedIndex = -1;

        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const q = searchInput.value.trim();
            if (q.length < 2) { closeList(); return; }

            debounceTimer = setTimeout(() => {
                fetch(`/agenda/buscar-clientes/?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => renderList(data.clientes || []))
                    .catch(() => closeList());
            }, 280);
        });

        function renderList(clientes) {
            list.innerHTML = '';
            selectedIndex = -1;
            if (clientes.length === 0) { closeList(); return; }

            clientes.forEach((c, idx) => {
                const li = document.createElement('li');
                li.setAttribute('data-nome', c.nome);
                li.setAttribute('data-telefone', c.telefone || '');
                li.setAttribute('data-index', idx);
                li.style.cssText = `
                    padding: 10px 14px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    border-bottom: 1px solid #f0f0f0;
                    transition: background 0.15s;
                `;
                li.innerHTML = `
                    <span style="font-weight:500;color:#333;">${c.nome}</span>
                    ${c.telefone ? `<span style="font-size:11px;color:#999;">${c.telefone}</span>` : ''}
                `;
                li.addEventListener('mouseenter', () => { li.style.background = '#dce8f7'; });
                li.addEventListener('mouseleave', () => { li.style.background = ''; });
                li.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    selectCliente(c.nome, c.telefone || '');
                });
                list.appendChild(li);
            });
            list.style.display = 'block';
        }

        function selectCliente(nome, telefone) {
            searchInput.value = nome;
            if (telefoneInput && !telefoneInput.value) telefoneInput.value = telefone;
            closeList();
        }

        function closeList() {
            list.style.display = 'none';
            list.innerHTML = '';
            selectedIndex = -1;
        }

        searchInput.addEventListener('keydown', function (e) {
            const items = list.querySelectorAll('li');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                highlightItem(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                highlightItem(items);
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                const li = items[selectedIndex];
                selectCliente(li.dataset.nome, li.dataset.telefone);
            } else if (e.key === 'Escape') {
                closeList();
            }
        });

        function highlightItem(items) {
            items.forEach((li, i) => {
                li.style.background = i === selectedIndex ? '#dce8f7' : '';
            });
            if (items[selectedIndex]) {
                items[selectedIndex].scrollIntoView({ block: 'nearest' });
            }
        }

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !list.contains(e.target)) {
                closeList();
            }
        });
    })();

    // ========== AUTOCOMPLETE DE CLIENTE (EDITAR AGENDAMENTO) ==========
    (function () {
        const searchInput = document.getElementById('edit_cliente_search');
        const telefoneInput = document.getElementById('edit_cliente_telefone');
        const list = document.getElementById('edit-cliente-autocomplete-list');
        if (!searchInput || !list) return;

        let debounceTimer = null;
        let selectedIndex = -1;

        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const q = searchInput.value.trim();
            if (q.length < 2) { closeList(); return; }

            debounceTimer = setTimeout(() => {
                fetch(`/agenda/buscar-clientes/?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => renderList(data.clientes || []))
                    .catch(() => closeList());
            }, 280);
        });

        function renderList(clientes) {
            list.innerHTML = '';
            selectedIndex = -1;
            if (clientes.length === 0) { closeList(); return; }

            clientes.forEach((c, idx) => {
                const li = document.createElement('li');
                li.setAttribute('data-nome', c.nome);
                li.setAttribute('data-telefone', c.telefone || '');
                li.setAttribute('data-index', idx);
                li.style.cssText = `
                    padding: 10px 14px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    border-bottom: 1px solid #f0f0f0;
                    transition: background 0.15s;
                `;
                li.innerHTML = `
                    <span style="font-weight:500;color:#333;">${c.nome}</span>
                    ${c.telefone ? `<span style="font-size:11px;color:#999;">${c.telefone}</span>` : ''}
                `;
                li.addEventListener('mouseenter', () => { li.style.background = '#dce8f7'; });
                li.addEventListener('mouseleave', () => { li.style.background = ''; });
                li.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    selectCliente(c.nome, c.telefone || '');
                });
                list.appendChild(li);
            });
            list.style.display = 'block';
        }

        function selectCliente(nome, telefone) {
            searchInput.value = nome;
            if (telefoneInput && !telefoneInput.value) telefoneInput.value = telefone;
            closeList();
        }

        function closeList() {
            list.style.display = 'none';
            list.innerHTML = '';
            selectedIndex = -1;
        }

        searchInput.addEventListener('keydown', function (e) {
            const items = list.querySelectorAll('li');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                highlightItem(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                highlightItem(items);
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                const li = items[selectedIndex];
                selectCliente(li.dataset.nome, li.dataset.telefone);
            } else if (e.key === 'Escape') {
                closeList();
            }
        });

        function highlightItem(items) {
            items.forEach((li, i) => {
                li.style.background = i === selectedIndex ? '#dce8f7' : '';
            });
            if (items[selectedIndex]) {
                items[selectedIndex].scrollIntoView({ block: 'nearest' });
            }
        }

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !list.contains(e.target)) {
                closeList();
            }
        });
    })();

    // ========== REAGENDAMENTO AUTOMÁTICO ==========
    (function () {
        const btnReagendar = document.querySelectorAll('.btn-reagendar');
        const inputDias = document.getElementById('reagendar_dias');
        const infoBox = document.getElementById('reagendar_info');

        btnReagendar.forEach(btn => {
            btn.addEventListener('click', function () {
                const dias = this.dataset.dias;
                const jaSelecionado = inputDias.value === dias;

                // Toggle: clicou no mesmo = desmarcar
                if (jaSelecionado) {
                    inputDias.value = '';
                    infoBox.style.display = 'none';
                    btnReagendar.forEach(b => {
                        b.style.background = 'var(--bg)';
                        b.style.color = 'var(--text-muted)';
                        b.style.borderColor = 'var(--border)';
                    });
                    const c = document.getElementById('reagendar_dias_custom');
                    if (c) c.value = '';
                    return;
                }

                inputDias.value = dias;
                const c = document.getElementById('reagendar_dias_custom');
                if (c) c.value = '';

                // Calcula a data provável
                const dataAtualStr = document.getElementById('finalizar_agendamento_id')
                    ? (() => {
                        const hiddenData = document.getElementById('edit_data_horario');
                        if (hiddenData && hiddenData.value) {
                            const d = new Date(hiddenData.value);
                            d.setDate(d.getDate() + parseInt(dias));
                            return d.toLocaleDateString('pt-BR');
                        }
                        const d = new Date();
                        d.setDate(d.getDate() + parseInt(dias));
                        return d.toLocaleDateString('pt-BR');
                    })()
                    : (() => {
                        const d = new Date();
                        d.setDate(d.getDate() + parseInt(dias));
                        return d.toLocaleDateString('pt-BR');
                    })();

                infoBox.textContent = `Próximo agendamento em ${dias} dias (aprox. ${dataAtualStr})`;
                infoBox.style.display = 'block';

                // Destacar botão selecionado
                btnReagendar.forEach(b => {
                    b.style.background = 'var(--bg)';
                    b.style.color = 'var(--text-muted)';
                    b.style.borderColor = 'var(--border)';
                });
                this.style.background = 'rgba(37, 99, 235, 0.1)';
                this.style.color = '#2563eb';
                this.style.borderColor = 'rgba(37, 99, 235, 0.4)';
            });
        });

        // Input customizado de dias
        const inputCustom = document.getElementById('reagendar_dias_custom');
        if (inputCustom) {
            inputCustom.addEventListener('input', function () {
                const dias = parseInt(this.value);

                // Desmarcar botões de atalho
                btnReagendar.forEach(b => {
                    b.style.background = 'var(--bg)';
                    b.style.color = 'var(--text-muted)';
                    b.style.borderColor = 'var(--border)';
                });

                if (!dias || dias < 1) {
                    inputDias.value = '';
                    infoBox.style.display = 'none';
                    return;
                }

                inputDias.value = dias;
                const d = new Date();
                d.setDate(d.getDate() + dias);
                infoBox.textContent = `Próximo agendamento em ${dias} dias (aprox. ${d.toLocaleDateString('pt-BR')})`;
                infoBox.style.display = 'block';
            });
        }

        // Resetar ao abrir o modal de finalizar
        const modalFinalizar = document.getElementById('modal-finalizar-atendimento');
        if (modalFinalizar) {
            const observer = new MutationObserver(() => {
                if (!modalFinalizar.classList.contains('active')) {
                    inputDias.value = '';
                    if (infoBox) infoBox.style.display = 'none';
                    if (inputCustom) inputCustom.value = '';
                    btnReagendar.forEach(b => {
                        b.style.background = 'var(--bg)';
                        b.style.color = 'var(--text-muted)';
                        b.style.borderColor = 'var(--border)';
                    });
                }
            });
            observer.observe(modalFinalizar, { attributes: true, attributeFilter: ['class'] });
        }
    })();

});
