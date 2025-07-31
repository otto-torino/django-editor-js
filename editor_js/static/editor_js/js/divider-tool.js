class DividerTool {
    static get toolbox() {
        return {
            title: 'Divider',
            icon: '<svg width="20" height="20" viewBox="0 0 20 20"><line x1="0" y1="10" x2="20" y2="10" stroke="currentColor" stroke-width="2"/></svg>'
        };
    }

    render() {
        const hr = document.createElement('hr');
        return hr;
    }

    save(blockContent) {
        return {};
    }
}

window.DividerTool = DividerTool;