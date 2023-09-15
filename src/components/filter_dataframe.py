import streamlit as st
from st_aggrid import (
    GridOptionsBuilder,
    AgGrid,
    GridUpdateMode,
    DataReturnMode,
    JsCode,
    ColumnsAutoSizeMode,
)


def draw_aggrid(df) -> AgGrid:
    # Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)

    # customize gridOptions

    cell_renderer = JsCode(
        """
        class UrlCellRenderer {
          init(params) {
            this.eGui = document.createElement('a');
            this.eGui.innerText = params.value.split('[').pop().split(']')[0];
            this.eGui.setAttribute('href', params.value.split('(').pop().split(')')[0]);
            this.eGui.setAttribute('style', "text-decoration:none");
            this.eGui.setAttribute('target', "_blank");
          }
          getGui() {
            return this.eGui;
          }
        }
    """
    )

    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_columns("Summary", wrapText=True)
    gb.configure_columns("Summary", autoHeight=True, width=300)
    gb.configure_columns(
        "Date",
        autoHeight=True,
        autoWidth=True,
        type=["customDateTimeFormat"],
        custom_format_string="yyyy/MM/dd",
    )
    gb.configure_columns("Score", autoHeight=True, autoWidth=True)
    gb.configure_grid_options(domLayout="normal")
    gb.configure_column("Title", cellRenderer=cell_renderer, wrapText=True)
    gb.configure_column("TextSearch", hide=True)
    gb.configure_column("compound", hide=True)
    gb.configure_column("YearMonth", hide=True)
    gb.configure_column("Main", hide=True)
    gb.configure_column("Link", hide=True)
    # gb.configure_default_column(floatingFilter=True)
    gridOptions = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        key="dataframe",
        width="200%",
        height=600,
        data_return_mode="FILTERED",
        update_mode="MODEL_CHANGED",
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,  # Set it to True to allow jsfunction to be injected
        enable_enterprise_modules=True,
        reload_data=True,
        custom_css={"#gridToolBar": {"padding-bottom": "0px !important"}},
    )

    return grid_response
