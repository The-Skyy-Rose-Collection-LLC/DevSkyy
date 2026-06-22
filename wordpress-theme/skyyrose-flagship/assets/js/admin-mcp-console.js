/**
 * DevSkyy MCP Console (wp-admin)
 *
 * Lists and invokes MCP tools via the admin-ajax relay (skyyrose_mcp_invoke).
 * All DOM built with createElement/textContent — no innerHTML.
 *
 * @package SkyyRose_Flagship
 * @since   1.2.0
 */
( function () {
	'use strict';

	var cfg = window.skyyroseMcp || {};
	var i18n = cfg.i18n || {};

	var toolSel = document.getElementById( 'skyyrose-mcp-tool' );
	var argsEl = document.getElementById( 'skyyrose-mcp-args' );
	var statusEl = document.getElementById( 'skyyrose-mcp-status' );
	var resultEl = document.getElementById( 'skyyrose-mcp-result' );
	var refreshBtn = document.getElementById( 'skyyrose-mcp-refresh' );
	var invokeBtn = document.getElementById( 'skyyrose-mcp-invoke' );

	if ( ! toolSel || ! argsEl || ! resultEl ) {
		return;
	}

	function setStatus( msg ) {
		statusEl.textContent = msg || '';
	}

	function setResult( value ) {
		resultEl.textContent = ( typeof value === 'string' ) ? value : JSON.stringify( value, null, 2 );
	}

	function post( params ) {
		var body = new URLSearchParams();
		body.append( 'action', 'skyyrose_mcp_invoke' );
		body.append( 'nonce', cfg.nonce || '' );
		Object.keys( params ).forEach( function ( key ) {
			body.append( key, params[ key ] );
		} );

		return fetch( cfg.ajaxUrl, {
			method: 'POST',
			credentials: 'same-origin',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: body.toString()
		} ).then( function ( response ) {
			return response.json();
		} );
	}

	function errorMessage( res ) {
		return ( res && res.data && res.data.message ) ? res.data.message : 'Request failed.';
	}

	function loadTools() {
		setStatus( i18n.loading );
		post( { mcp_action: 'list' } ).then( function ( res ) {
			setStatus( '' );
			if ( ! res || ! res.success ) {
				setResult( errorMessage( res ) );
				return;
			}

			var tools = ( res.data && res.data.tools ) || [];
			while ( toolSel.firstChild ) {
				toolSel.removeChild( toolSel.firstChild );
			}

			if ( ! tools.length ) {
				setStatus( i18n.noTools );
				return;
			}

			tools.forEach( function ( tool ) {
				var opt = document.createElement( 'option' );
				opt.value = tool.name;
				opt.textContent = tool.description ? ( tool.name + ' — ' + tool.description ) : tool.name;
				toolSel.appendChild( opt );
			} );

			setStatus( ( i18n.toolsLoaded || '%d tools loaded.' ).replace( '%d', String( tools.length ) ) );
		} ).catch( function ( err ) {
			setStatus( '' );
			setResult( String( err ) );
		} );
	}

	function invoke() {
		var tool = toolSel.value;
		if ( ! tool ) {
			setResult( i18n.selectTool || 'Select a tool first.' );
			return;
		}

		var argsText = ( argsEl.value || '{}' ).trim() || '{}';
		try {
			JSON.parse( argsText );
		} catch ( err ) {
			setResult( i18n.invalidJson || 'Invalid JSON.' );
			return;
		}

		setStatus( i18n.loading );
		post( { mcp_action: 'call', tool: tool, args: argsText } ).then( function ( res ) {
			setStatus( '' );
			setResult( ( res && res.success ) ? res.data : errorMessage( res ) );
		} ).catch( function ( err ) {
			setStatus( '' );
			setResult( String( err ) );
		} );
	}

	if ( refreshBtn ) {
		refreshBtn.addEventListener( 'click', loadTools );
	}
	if ( invokeBtn ) {
		invokeBtn.addEventListener( 'click', invoke );
	}

	loadTools();
}() );
