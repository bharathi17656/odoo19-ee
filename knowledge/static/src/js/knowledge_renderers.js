import { FormRenderer } from "@web/views/form/form_renderer";
import { useExternalListener, useRef, useSubEnv } from "@odoo/owl";

export class KnowledgeArticleFormRenderer extends FormRenderer {

    //--------------------------------------------------------------------------
    // Component
    //--------------------------------------------------------------------------
    setup() {
        super.setup();
        const rootRef = useRef("compiled_view_root");
        useSubEnv({
            onTopEmbeddedViewChange: (isTopEmbeddedView) =>
                rootRef.el
                    ?.querySelector(".o_knowledge_body")
                    ?.classList.toggle("o_knowledge_body_top_embedded_view", isTopEmbeddedView),
        });
        useExternalListener(document, "click", event => {
            if (event.target.classList.contains("o_nocontent_create_btn")) {
                this.env.createArticle("private");
            }
        });
    }
}
